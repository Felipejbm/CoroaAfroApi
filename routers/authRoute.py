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
    MentorDB,
    PasswordResetDB,
    MentorSolicitacaoDB,
    )
from services.company_identity import usuario_vinculado
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
    LoginReq,
    PasswordResetRequest,
    PasswordResetConfirm,
    )

router = APIRouter(prefix="/auth", tags=["Auth"])

RESET_EXPIRATION_MINUTES = 10
RESET_MAX_ATTEMPTS = 5

def clear_sessions(request, db):
    cookie = request.cookies.get(COOKIE_NAME)
    if cookie:
        for model in (AuthSessionDB, MentorSessionDB):
            session = db.get(model, token_hash(cookie))
            if session:
                db.delete(session)


def _normalizar_email(email: str) -> str:
    return email.strip().lower()


def _conta_por_email(db: Session, email: str, papel: str):
    if papel == "mentor":
        return db.query(MentorAccessDB).filter(MentorAccessDB.email == email).with_for_update().first()
    return db.query(EmpreendedorDB).filter(EmpreendedorDB.email == email).with_for_update().first()


def recuperacao_local(request: Request):
    # Não há transporte de e-mail neste fluxo. Nunca retorne códigos em ambiente público.
    if not get_settings().password_reset_demo_mode or not request.client or request.client.host not in {"127.0.0.1", "::1"}:
        raise HTTPException(503, "A recuperação por e-mail ainda não está configurada.")


@router.post("/password-reset/request", dependencies=[Depends(validate_origin), Depends(recuperacao_local)])
def solicitar_redefinicao(dados: PasswordResetRequest, db: Session = Depends(get_db)):
    email = _normalizar_email(dados.email)
    conta = _conta_por_email(db, email, dados.papel)
    resposta = {"message": "Se a conta estiver cadastrada, um código de recuperação foi gerado."}

    if not conta or (dados.papel == "mentor" and not conta.ativo):
        return resposta
    recentes = db.query(PasswordResetDB).filter(PasswordResetDB.email == email, PasswordResetDB.papel == dados.papel, PasswordResetDB.criado_em > datetime.utcnow() - timedelta(hours=1)).count()
    if recentes >= 5:
        return resposta

    db.query(PasswordResetDB).filter(
        PasswordResetDB.email == email,
        PasswordResetDB.papel == dados.papel,
        PasswordResetDB.usado.is_(False),
    ).update({"usado": True}, synchronize_session=False)

    codigo = f"{secrets.randbelow(1_000_000):06d}"
    db.add(PasswordResetDB(
        email=email,
        papel=dados.papel,
        codigo_hash=token_hash(codigo),
        expires_at=datetime.utcnow() + timedelta(minutes=RESET_EXPIRATION_MINUTES),
    ))
    db.commit()

    if get_settings().password_reset_demo_mode:
        resposta["demo_code"] = codigo
    return resposta


@router.post("/password-reset/confirm", dependencies=[Depends(validate_origin), Depends(recuperacao_local)])
def confirmar_redefinicao(dados: PasswordResetConfirm, db: Session = Depends(get_db)):
    email = _normalizar_email(dados.email)
    conta = _conta_por_email(db, email, dados.papel)
    redefinicao = db.query(PasswordResetDB).filter(
        PasswordResetDB.email == email,
        PasswordResetDB.papel == dados.papel,
        PasswordResetDB.usado.is_(False),
    ).order_by(PasswordResetDB.id.desc()).with_for_update().first()

    if not redefinicao or redefinicao.expires_at < datetime.utcnow():
        raise HTTPException(400, "Código inválido ou expirado. Solicite um novo código.")
    if redefinicao.tentativas >= RESET_MAX_ATTEMPTS:
        redefinicao.usado = True
        db.commit()
        raise HTTPException(400, "Limite de tentativas atingido. Solicite um novo código.")
    if not secrets.compare_digest(redefinicao.codigo_hash, token_hash(dados.codigo)):
        redefinicao.tentativas += 1
        db.commit()
        raise HTTPException(400, "Código inválido ou expirado. Solicite um novo código.")

    if not conta or (dados.papel == "mentor" and not conta.ativo):
        redefinicao.usado = True
        db.commit()
        raise HTTPException(400, "Código inválido ou expirado. Solicite um novo código.")

    if dados.papel == "mentor":
        conta.senha_hash = hash_password(dados.nova_senha)
        db.query(MentorSessionDB).filter(MentorSessionDB.id_mentor == conta.id_mentor).delete()
    else:
        conta.senha = hash_password(dados.nova_senha)
        legado = usuario_vinculado(db, conta)
        if legado:
            legado.senha = conta.senha
        db.query(AuthSessionDB).filter(AuthSessionDB.id_empreendedor == conta.id_empreendedor).delete()
    redefinicao.usado = True
    db.commit()
    return {"message": "Senha redefinida com sucesso."}


@router.post("/login", dependencies=[Depends(validate_origin)])
def logar(dados: LoginReq, request: Request, response: Response, db: Session = Depends(get_db)):
    if dados.papel == "mentor":
        access = db.query(MentorAccessDB).filter(MentorAccessDB.email == dados.email.strip().lower()).first()

        if not access:
            solicitacao = db.query(MentorSolicitacaoDB).filter_by(email=dados.email.strip().lower()).first()
            if solicitacao and verify_password(dados.senha, solicitacao.senha_hash):
                if solicitacao.status == "pendente":
                    raise HTTPException(403, "Sua solicitação de mentor ainda está em análise.")
                if solicitacao.status == "recusada":
                    raise HTTPException(403, solicitacao.motivo_recusa or "Sua solicitação de mentor não foi aprovada.")
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
            samesite=get_settings().session_cookie_samesite,
            path="/"
            )
        response.headers["Cache-Control"] = "no-store"

        return {
            "Msg": "Login realizado com sucesso!",
            "Usuario": MentorPublic(
                id=mentor.id_mentor,
                administrador=access.administrador if access else False,
                nome=mentor.nome,
                email=access.email,
                especialidade=mentor.especialidade,
                biografia=mentor.biografia,
            ),
        }

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
        samesite=get_settings().session_cookie_samesite,
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
            id=mentor.id_mentor,
                administrador=access.administrador if access else False,
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
    response.delete_cookie(COOKIE_NAME, path="/", samesite=get_settings().session_cookie_samesite,
                           secure=get_settings().session_cookie_secure, httponly=True)
    return {"Msg": "Sessão encerrada."}
