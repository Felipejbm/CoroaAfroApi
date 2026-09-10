"""Perfil próprio e gestão de mentores com autorização no servidor."""
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
from dependencies import get_current_mentor
from models import MentorDB, MentorAccessDB, MentorSessionDB
from security import hash_password

router = APIRouter(prefix="/mentoria", tags=["Perfil e administração"])

class PerfilEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    nome: str = Field(min_length=1, max_length=255)
    email: EmailStr = Field(max_length=255)
    especialidade: str = Field(min_length=1, max_length=50)
    biografia: str = Field(default="", max_length=5000)

class NovoMentor(PerfilEntrada):
    senha: str = Field(min_length=12, max_length=128)

class AcessoEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ativo: bool = Field(strict=True)

def publico(m, a):
    return {"id": m.id_mentor, "nome": m.nome, "email": a.email,
            "especialidade": m.especialidade, "biografia": m.biografia,
            "administrador": a.administrador, "ativo": a.ativo, "papel": "mentor"}

def administrador(mentor=Depends(get_current_mentor), db: Session=Depends(get_db)):
    access = db.get(MentorAccessDB, mentor.id_mentor)
    if not access or not access.administrador:
        raise HTTPException(403, "Acesso restrito à administração.")
    return mentor

@router.get("/perfil")
def perfil(response: Response, mentor=Depends(get_current_mentor), db: Session=Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    return publico(mentor, db.get(MentorAccessDB, mentor.id_mentor))

@router.patch("/perfil")
def editar(dados: PerfilEntrada, mentor=Depends(get_current_mentor), db: Session=Depends(get_db)):
    access = db.get(MentorAccessDB, mentor.id_mentor)
    mentor.nome, mentor.especialidade, mentor.biografia = dados.nome, dados.especialidade, dados.biografia
    access.email = str(dados.email).lower()
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Este e-mail já está associado a outro mentor.") from None
    return publico(mentor, access)

@router.get("/admin/mentores")
def listar(response: Response, admin=Depends(administrador), db: Session=Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    return [publico(m,a) for m,a in db.query(MentorDB,MentorAccessDB).join(MentorAccessDB, MentorAccessDB.id_mentor==MentorDB.id_mentor).order_by(MentorDB.nome).all()]

@router.post("/admin/mentores", status_code=201)
def criar(dados: NovoMentor, admin=Depends(administrador), db: Session=Depends(get_db)):
    mentor = MentorDB(nome=dados.nome, especialidade=dados.especialidade, biografia=dados.biografia)
    try:
        db.add(mentor)
        db.flush()
        access = MentorAccessDB(id_mentor=mentor.id_mentor, email=str(dados.email).lower(), senha_hash=hash_password(dados.senha), ativo=True, administrador=False)
        db.add(access)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Já existe mentor cadastrado com este e-mail.") from None
    return publico(mentor, access)

@router.patch("/admin/mentores/{mentor_id}/acesso")
def acesso(mentor_id: int, dados: AcessoEntrada, admin=Depends(administrador), db: Session=Depends(get_db)):
    access = db.query(MentorAccessDB).filter_by(id_mentor=mentor_id).with_for_update().first()
    mentor = db.get(MentorDB, mentor_id)
    if not access or not mentor:
        raise HTTPException(404, "Mentor não encontrado.")
    if access.administrador:
        raise HTTPException(409, "O acesso de administradores não pode ser alterado por esta tela.")
    access.ativo = dados.ativo
    if not dados.ativo:
        db.query(MentorSessionDB).filter_by(id_mentor=mentor_id).delete()
    db.commit()
    return publico(mentor, access)
