from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
from models import MentorAccessDB, MentorSolicitacaoDB
from security import hash_password, validate_origin

router = APIRouter(prefix="/mentor-solicitacoes", tags=["Solicitações de mentor"])

class SolicitacaoEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    nome: str = Field(min_length=3, max_length=255)
    email: EmailStr = Field(max_length=255)
    senha: str = Field(min_length=8, max_length=128)
    especialidade: str = Field(min_length=2, max_length=50)
    biografia: str = Field(min_length=20, max_length=2000)

@router.post("", status_code=201, dependencies=[Depends(validate_origin)])
def solicitar(dados: SolicitacaoEntrada, db: Session = Depends(get_db)):
    email = dados.email.lower()
    if db.query(MentorAccessDB).filter_by(email=email).first():
        raise HTTPException(409, "Este e-mail já pertence a um mentor autorizado.")
    existente = db.query(MentorSolicitacaoDB).filter_by(email=email).first()
    if existente and existente.status in {"pendente", "aprovada"}:
        raise HTTPException(409, "Já existe uma solicitação para este e-mail.")
    if existente:
        existente.nome, existente.senha_hash = dados.nome, hash_password(dados.senha)
        existente.especialidade, existente.biografia = dados.especialidade, dados.biografia
        existente.status, existente.motivo_recusa, existente.analisada_em = "pendente", None, None
    else:
        db.add(MentorSolicitacaoDB(nome=dados.nome, email=email, senha_hash=hash_password(dados.senha), especialidade=dados.especialidade, biografia=dados.biografia))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Já existe uma solicitação para este e-mail.") from None
    return {"message": "Solicitação enviada para análise."}
