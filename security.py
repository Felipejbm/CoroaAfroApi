import hashlib
import hmac
import secrets
from datetime import datetime

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from config import get_settings
from database import get_db
from models import AuthSessionDB, EmpreendedorDB, MentorSessionDB, MentorAccessDB, MentorDB

COOKIE_NAME = "coroa_session"
PASSWORD_ITERATIONS = 600_000


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    if not stored.startswith("pbkdf2_sha256$"):
        # Compatibilidade temporária: contas antigas são migradas ao fazer login.
        return hmac.compare_digest(password.encode(), stored.encode())
    try:
        _, iterations, salt, expected = stored.split("$")
        rounds = int(iterations)
        if rounds < 1 or rounds > 1_000_000:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), rounds)
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


def validate_origin(request: Request):
    origin = request.headers.get("origin")
    own_origin = str(request.base_url).rstrip("/")
    if origin and origin not in {get_settings().frontend_origin.rstrip("/"), own_origin}:
        raise HTTPException(403, "Origem da solicitação não autorizada.")
    if not origin and request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "Origem da solicitação não autorizada.")


def get_auth_session(request: Request, db: Session = Depends(get_db)) -> AuthSessionDB:
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        validate_origin(request)
    cookie = request.cookies.get(COOKIE_NAME, "")
    session = db.get(AuthSessionDB, token_hash(cookie)) if cookie else None
    if not session or session.expires_at <= datetime.utcnow():
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


def public_user(user: EmpreendedorDB) -> dict:
    return {
        "papel": "empreendedor",
        "id": user.id_empreendedor,
        "nome": user.nome,
        "email": user.email,
        "telefone": user.telefone,
        "data_cadastro": user.data_cadastro,
    }


def get_current_mentor(request: Request, db: Session = Depends(get_db)) -> MentorDB:
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        validate_origin(request)
    cookie = request.cookies.get(COOKIE_NAME, "")
    session = db.get(MentorSessionDB, token_hash(cookie)) if cookie else None
    if not session or session.expires_at <= datetime.utcnow():
        raise HTTPException(401, "Entre com uma conta de mentor autorizada.")
    access = db.get(MentorAccessDB, session.id_mentor)
    mentor = db.get(MentorDB, session.id_mentor)
    if not access or not access.ativo or not mentor:
        raise HTTPException(403, "O acesso deste mentor está desativado.")
    return mentor


def public_mentor(mentor: MentorDB, access: MentorAccessDB) -> dict:
    return {"id": mentor.id_mentor, "nome": mentor.nome, "email": access.email,
            "papel": "mentor", "especialidade": mentor.especialidade, "biografia": mentor.biografia}


def require_migrated_module(request: Request, db: Session = Depends(get_db)):
    """Fail closed until legacy records have ownership and role authorization."""
    cookie = request.cookies.get(COOKIE_NAME, "")
    if cookie and db.get(MentorSessionDB, token_hash(cookie)):
        get_current_mentor(request, db)
    else:
        get_current_user(get_auth_session(request, db), db)
    raise HTTPException(503, "Este módulo está em integração. Nenhum dado foi alterado.")
