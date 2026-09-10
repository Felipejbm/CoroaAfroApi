"""Recuperação por link compatível com as telas de login e perfil."""
import secrets
from datetime import datetime, timedelta
from typing import Literal
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from config import get_settings
from models import PasswordResetTokenDB, EmpreendedorDB, MentorAccessDB, MentorDB, AuthSessionDB, MentorSessionDB
from security import COOKIE_NAME, hash_password, token_hash, validate_origin
from services.company_identity import usuario_vinculado
from services.password_reset_email import configured, send_reset_email

router = APIRouter(prefix="/auth", tags=["Auth"], dependencies=[Depends(validate_origin)])
GENERIC = {"mensagem": "Se houver uma conta com esses dados, você receberá um link de segurança."}


class SolicitarLink(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    email: EmailStr = Field(max_length=255)
    papel: Literal["mentor", "empreendedor"] = "empreendedor"


class RedefinirSenha(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")
    senha: str = Field(min_length=12, max_length=128)

    @field_validator("senha")
    @classmethod
    def senha_valida(cls, value):
        if len(value.strip()) < 12:
            raise ValueError("Use pelo menos 12 caracteres além de espaços nas extremidades.")
        return value


def email_hash(papel, email):
    return token_hash(papel + ":" + email.strip().lower())


@router.post("/recuperar-senha", status_code=202)
def solicitar(dados: SolicitarLink, request: Request, response: Response,
              background: BackgroundTasks, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    if not configured():
        raise HTTPException(503, "O envio de e-mail ainda não está disponível. Tente novamente mais tarde.")
    now = datetime.utcnow()
    email = str(dados.email).lower()
    hashed_email = email_hash(dados.papel, email)
    # Não confia em cabeçalhos de proxy enviados diretamente pelo cliente.
    hashed_ip = token_hash(request.client.host if request.client else "unknown")
    recent = db.query(PasswordResetTokenDB).filter(PasswordResetTokenDB.criado_em >= now - timedelta(hours=1))
    if recent.filter_by(email_hash=hashed_email).count() >= 5 or recent.filter_by(ip_hash=hashed_ip).count() >= 20:
        return GENERIC
    model = MentorAccessDB if dados.papel == "mentor" else EmpreendedorDB
    conta = db.query(model).filter(func.lower(model.email) == email).first()
    if conta is not None and dados.papel == "mentor" and (not conta.ativo or db.get(MentorDB, conta.id_mentor) is None):
        conta = None
    raw = secrets.token_urlsafe(32)
    account_id = None
    fingerprint = None
    if conta is not None:
        account_id = conta.id_mentor if dados.papel == "mentor" else conta.id_empreendedor
        fingerprint = token_hash(conta.senha_hash if dados.papel == "mentor" else conta.senha)
    db.add(PasswordResetTokenDB(token_hash=token_hash(raw), papel=dados.papel,
        conta_id=account_id, email_hash=hashed_email, ip_hash=hashed_ip,
        senha_fingerprint=fingerprint, criado_em=now, expires_at=now + timedelta(minutes=30)))
    db.commit()
    if conta is not None:
        background.add_task(send_reset_email, email, raw)
    return GENERIC


@router.post("/redefinir-senha")
def redefinir(dados: RedefinirSenha, response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    invalid = HTTPException(400, "Link inválido ou expirado. Solicite um novo link.")
    reset = db.query(PasswordResetTokenDB).filter_by(token_hash=token_hash(dados.token)).with_for_update().first()
    now = datetime.utcnow()
    if reset is None or reset.usado_em is not None or reset.expires_at <= now or reset.conta_id is None:
        raise invalid
    if reset.papel not in {"mentor", "empreendedor"}:
        raise invalid
    mentor = reset.papel == "mentor"
    model = MentorAccessDB if mentor else EmpreendedorDB
    key = model.id_mentor if mentor else model.id_empreendedor
    conta = db.query(model).filter(key == reset.conta_id).with_for_update().first()
    if conta is None or (mentor and (not conta.ativo or db.get(MentorDB, conta.id_mentor) is None)):
        raise invalid
    current = conta.senha_hash if mentor else conta.senha
    if reset.senha_fingerprint != token_hash(current) or reset.email_hash != email_hash(reset.papel, conta.email):
        raise invalid
    hashed = hash_password(dados.senha)
    if mentor:
        conta.senha_hash = hashed
        db.query(MentorSessionDB).filter_by(id_mentor=conta.id_mentor).delete()
    else:
        conta.senha = hashed
        legado = usuario_vinculado(db, conta)
        if legado is not None:
            legado.senha = hashed
        db.query(AuthSessionDB).filter_by(id_empreendedor=conta.id_empreendedor).delete()
    reset.usado_em = now
    db.commit()
    cfg = get_settings()
    response.delete_cookie(COOKIE_NAME, path="/", httponly=True,
                           secure=cfg.session_cookie_secure, samesite=cfg.session_cookie_samesite)
    return {"mensagem": "Senha redefinida com sucesso. Entre novamente."}
