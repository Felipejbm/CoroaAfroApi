import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from config import get_settings
from models import PasswordResetDB, EmpreendedorDB, MentorAccessDB, MentorDB, AuthSessionDB, MentorSessionDB
from security import token_hash, hash_password, validate_origin, COOKIE_NAME
from services.email_service import email_configurado, enviar_redefinicao
from services.company_identity import usuario_vinculado

router = APIRouter(prefix='/auth', tags=['Redefinição de senha'], dependencies=[Depends(validate_origin)])
AVISO = 'Se houver uma conta ativa com esses dados, você receberá um link de segurança por e-mail. Confira também o spam.'

def agora():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Solicitacao(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    email: EmailStr = Field(max_length=255)
    papel: Literal['empreendedor', 'mentor'] = 'empreendedor'

class Redefinicao(BaseModel):
    model_config = ConfigDict(extra='forbid')
    token: str = Field(min_length=43, max_length=43, pattern=r'^[A-Za-z0-9_-]+$')
    senha: str = Field(min_length=12, max_length=128)

@router.post('/recuperar-senha', status_code=202)
def solicitar(dados: Solicitacao, request: Request, response: Response, tarefas: BackgroundTasks, db: Session = Depends(get_db)):
    response.headers['Cache-Control'] = 'no-store'
    if not email_configurado():
        raise HTTPException(503, 'O envio de e-mail ainda não está disponível. Tente novamente mais tarde.')
    email = str(dados.email).lower()
    instante = agora()
    email_id = token_hash(dados.papel + ':' + email)
    ip_id = token_hash(request.client.host if request.client else 'desconhecido')
    recentes = db.query(PasswordResetDB).filter(PasswordResetDB.criado_em > instante - timedelta(hours=1))
    if recentes.filter_by(email_hash=email_id).count() >= 5 or recentes.filter_by(ip_hash=ip_id).count() >= 20:
        return {'mensagem': AVISO}
    conta = db.query(MentorAccessDB if dados.papel == 'mentor' else EmpreendedorDB).filter(
        func.lower(MentorAccessDB.email if dados.papel == 'mentor' else EmpreendedorDB.email) == email).first()
    if dados.papel == 'mentor' and conta and (not conta.ativo or db.get(MentorDB, conta.id_mentor) is None):
        conta = None
    token = secrets.token_urlsafe(32)
    senha_atual = (conta.senha_hash if dados.papel == 'mentor' else conta.senha) if conta else None
    db.add(PasswordResetDB(token_hash=token_hash(token), papel=dados.papel,
        conta_id=(conta.id_mentor if dados.papel == 'mentor' else conta.id_empreendedor) if conta else None,
        email_hash=email_id, ip_hash=ip_id, senha_fingerprint=token_hash(senha_atual) if senha_atual else None,
        criado_em=instante, expires_at=instante + timedelta(minutes=30)))
    db.commit()
    if conta:
        link = get_settings().frontend_origin.rstrip('/') + '/redefinir-senha#token=' + token
        tarefas.add_task(enviar_redefinicao, conta.email, link)
    return {'mensagem': AVISO}

@router.post('/redefinir-senha')
def redefinir(dados: Redefinicao, response: Response, db: Session = Depends(get_db)):
    response.headers['Cache-Control'] = 'no-store'
    if len(dados.senha.strip()) < 12:
        raise HTTPException(422, 'Use uma senha de 12 a 128 caracteres, sem contar espaços nas extremidades.')
    reset = db.query(PasswordResetDB).filter_by(token_hash=token_hash(dados.token)).with_for_update().first()
    if not reset or reset.usado_em or reset.expires_at <= agora() or reset.conta_id is None:
        raise HTTPException(400, 'Link inválido, expirado ou já utilizado. Solicite um novo link.')
    mentor = reset.papel == 'mentor'
    modelo = MentorAccessDB if mentor else EmpreendedorDB
    coluna = MentorAccessDB.id_mentor if mentor else EmpreendedorDB.id_empreendedor
    conta = db.query(modelo).filter(coluna == reset.conta_id).with_for_update().first()
    senha_atual = (conta.senha_hash if mentor else conta.senha) if conta else ''
    if (not conta or (mentor and (not conta.ativo or db.get(MentorDB, conta.id_mentor) is None))
        or token_hash(senha_atual) != reset.senha_fingerprint
        or token_hash(reset.papel + ':' + conta.email.lower()) != reset.email_hash):
        raise HTTPException(400, 'Link inválido, expirado ou já utilizado. Solicite um novo link.')
    nova_senha = hash_password(dados.senha)
    if mentor:
        conta.senha_hash = nova_senha
        db.query(MentorSessionDB).filter_by(id_mentor=reset.conta_id).delete()
    else:
        conta.senha = nova_senha
        vinculado = usuario_vinculado(db, conta)
        if vinculado:
            vinculado.senha = nova_senha
        db.query(AuthSessionDB).filter_by(id_empreendedor=reset.conta_id).delete()
    reset.usado_em = agora()
    db.commit()
    response.delete_cookie(COOKIE_NAME, path='/', secure=get_settings().session_cookie_secure, httponly=True, samesite='lax')
    return {'mensagem': 'Senha redefinida. Entre novamente com sua nova senha.'}
