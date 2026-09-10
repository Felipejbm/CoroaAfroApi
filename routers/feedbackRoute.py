from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_auth_session, get_current_mentor, get_current_user
from models import EmpreendedorDB, FeedbackDB, MentorDB, MentorSessionDB
from security import COOKIE_NAME, token_hash, validate_origin


router = APIRouter(prefix="/feedback", tags=["Feedback"])


class FeedbackEntrada(BaseModel):
    nota: int = Field(ge=1, le=5)
    comentario: str = Field(min_length=10, max_length=1000)
    autoriza_publicacao: bool = False


def participante(request: Request, db: Session = Depends(get_db)):
    cookie = request.cookies.get(COOKIE_NAME, "")
    if cookie and db.get(MentorSessionDB, token_hash(cookie)):
        pessoa = get_current_mentor(request, db)
        return "mentor", pessoa.id_mentor, pessoa.nome
    pessoa = get_current_user(get_auth_session(request, db), db)
    return "empreendedor", pessoa.id_empreendedor, pessoa.nome


def saida(item: FeedbackDB):
    return {
        "id": item.id_feedback,
        "nota": item.nota,
        "comentario": item.comentario,
        "autoriza_publicacao": item.autoriza_publicacao,
        "status": item.status,
        "criado_em": item.criado_em,
    }


@router.get("/me/status")
def meu_status(db: Session = Depends(get_db), ator=Depends(participante)):
    papel, autor_id, _ = ator
    ultimo = (
        db.query(FeedbackDB)
        .filter_by(autor_papel=papel, autor_id=autor_id)
        .order_by(FeedbackDB.criado_em.desc())
        .first()
    )
    pode_enviar = not ultimo or ultimo.criado_em <= datetime.utcnow() - timedelta(days=30)
    return {"pode_enviar": pode_enviar, "ultimo_feedback": saida(ultimo) if ultimo else None}


@router.post("", status_code=201, dependencies=[Depends(validate_origin)])
def criar(dados: FeedbackEntrada, db: Session = Depends(get_db), ator=Depends(participante)):
    papel, autor_id, nome = ator
    limite = datetime.utcnow() - timedelta(days=30)
    recente = db.query(FeedbackDB).filter(
        FeedbackDB.autor_papel == papel,
        FeedbackDB.autor_id == autor_id,
        FeedbackDB.criado_em > limite,
    ).first()
    if recente:
        raise HTTPException(409, "Você já enviou uma avaliação recentemente. Obrigado pela participação!")
    item = FeedbackDB(
        autor_papel=papel,
        autor_id=autor_id,
        autor_nome=nome,
        nota=dados.nota,
        comentario=dados.comentario.strip(),
        autoriza_publicacao=dados.autoriza_publicacao,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return saida(item)


@router.get("/publicos")
def publicos(db: Session = Depends(get_db)):
    itens = db.query(FeedbackDB).filter_by(status="aprovado", autoriza_publicacao=True).order_by(
        FeedbackDB.analisado_em.desc(), FeedbackDB.id_feedback.desc()
    ).limit(20).all()
    return [{"id": x.id_feedback, "nome": x.autor_nome.split()[0], "papel": x.autor_papel,
             "nota": x.nota, "comentario": x.comentario} for x in itens]
