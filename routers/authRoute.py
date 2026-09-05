import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from config import get_settings
from database import get_db
from models import (
    AuthSessionDB, 
    EmpreendedorDB, 
    MentorSessionDB, 
    MentorAccessDB, 
    MentorDB
    )
from security import (
    COOKIE_NAME, 
    hash_password,
    token_hash, 
    validate_origin,
    verify_password, 
)
from dependencies import (
    get_auth_session,
    get_current_user,
    get_current_mentor
)
from schemas.AuthSchema.AuthSchema import (
    MentorPublic, 
    EmpreendedorPublic, 
    LoginReq
    )

router = APIRouter(prefix="/auth", tags=["Auth"])

def clear_sessions(request, db):
    cookie = request.cookies.get(COOKIE_NAME)
    if cookie:
        for model in (AuthSessionDB, MentorSessionDB):
            session = db.get(model, token_hash(cookie))
            if session:
                db.delete(session)


@router.post("/login", dependencies=[Depends(validate_origin)])
def logar(dados: LoginReq, request: Request, response: Response, db: Session = Depends(get_db)):
    if dados.papel == "mentor":
        access = db.query(MentorAccessDB).filter(MentorAccessDB.email == dados.email.strip().lower()).first()

        if not access or not access.ativo or not verify_password(dados.senha, access.senha_hash):
            raise HTTPException(401, "E-mail ou senha incorretos, ou mentor não autorizado.")
        mentor = db.get(MentorDB, access.id_mentor)
        if not mentor:
            raise HTTPException(401, "Conta de mentor indisponível.")
        
        clear_sessions(request, db)
        token = secrets.token_urlsafe(32)
        db.add(MentorSessionDB(
            token_hash=token_hash(token), 
            id_mentor=mentor.id_mentor,
            expires_at=datetime.utcnow() + timedelta(hours=8)
            ))
        db.commit()
        response.set_cookie(
            COOKIE_NAME, 
            token, 
            max_age=8 * 3600, 
            httponly=True,
            secure=get_settings().session_cookie_secure, 
            samesite="lax", 
            path="/"
            )
        response.headers["Cache-Control"] = "no-store"

        return {"Msg": "Login realizado com sucesso!", "Usuario": MentorPublic(mentor, access)}
    
    user = db.query(EmpreendedorDB).filter(EmpreendedorDB.email == dados.email.strip()).first()

    if not user or not verify_password(dados.senha, user.senha):
        raise HTTPException(401, "E-mail ou senha incorretos.")
    if not user.senha.startswith("pbkdf2_sha256$"):
        user.senha = hash_password(dados.senha)

    clear_sessions(request, db)
    token = secrets.token_urlsafe(32)
    db.add(AuthSessionDB(
        token_hash=token_hash(token),
        id_empreendedor=user.id_empreendedor,
        expires_at=datetime.utcnow() + timedelta(hours=8),
    ))
    db.commit()
    response.set_cookie(
        COOKIE_NAME, 
        token, 
        max_age=8 * 3600, 
        httponly=True,
        secure=get_settings().session_cookie_secure, 
        samesite="lax", 
        path="/",
    )

    response.headers["Cache-Control"] = "no-store"

    return {
        "Msg": "Login realizado com sucesso!", 
        "Empreendedor": EmpreendedorPublic.model_validate(user)
        }


@router.get("/me")
def me(request: Request, response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    cookie = request.cookies.get(COOKIE_NAME, "")
    if cookie and db.get(MentorSessionDB, token_hash(cookie)):
        mentor = get_current_mentor(request, db)
        access = db.get(MentorAccessDB, mentor.id_mentor)

        return MentorPublic(
            id_mentor=mentor.id_mentor,
            nome=mentor.nome,
            email=access.email if access else "",
            especialidade=mentor.especialidade,
            biografia=mentor.biografia,
        )
    
    session = get_auth_session(request, db)
    user = get_current_user(session, db)

    return EmpreendedorPublic.model_validate(user)


@router.post("/logout", dependencies=[Depends(validate_origin)])
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    clear_sessions(request, db)
    db.commit()
    response.delete_cookie(COOKIE_NAME, path="/", samesite="lax",
                           secure=get_settings().session_cookie_secure, httponly=True)
    return {"Msg": "Sessão encerrada."}
