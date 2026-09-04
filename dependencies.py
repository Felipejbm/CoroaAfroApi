from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from models import AuthSessionDB, EmpreendedorDB, MentorAccessDB, MentorDB, MentorSessionDB
from security import COOKIE_NAME, token_hash, validate_origin

def get_auth_session(request: Request, db: Session = Depends(get_db)) -> AuthSessionDB:
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        validate_origin(request)
    
    cookie = request.cookies.get(COOKIE_NAME, "")
    session = db.get(AuthSessionDB, token_hash(cookie)) if cookie else None
    
    if not session or session.expires_at <= datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(401, "Sua sessão expirou. Faça login novamente.")
    return session


def get_current_user(
    session: AuthSessionDB = Depends(get_auth_session),
    db: Session = Depends(get_db),
) -> EmpreendedorDB:
    user = db.get(EmpreendedorDB, session.id_empreendedor)
    if not user:
        raise HTTPException(401, "Faça login novamente.")
    return user


def get_current_mentor(request: Request, db: Session = Depends(get_db)) -> MentorDB:
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        validate_origin(request)
        
    cookie = request.cookies.get(COOKIE_NAME, "")
    session = db.get(MentorSessionDB, token_hash(cookie)) if cookie else None
    
    if not session or session.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(401, "Entre com uma conta de mentor autorizada.")
        
    access = db.get(MentorAccessDB, session.id_mentor)
    mentor = db.get(MentorDB, session.id_mentor)
    
    if not access or not access.ativo or not mentor:
        raise HTTPException(403, "O acesso deste mentor está desativado.")
    return mentor


def require_migrated_module(request: Request, db: Session = Depends(get_db)):
    """Fail closed until legacy records have ownership and role authorization."""
    cookie = request.cookies.get(COOKIE_NAME, "")
    if cookie and db.get(MentorSessionDB, token_hash(cookie)):
        get_current_mentor(request, db)
    else:
        get_current_user(get_auth_session(request, db), db)
    raise HTTPException(503, "Este módulo está em integração. Nenhum dado foi alterado.")