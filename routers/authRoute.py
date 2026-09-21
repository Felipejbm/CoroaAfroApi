import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
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
    SocialSignupDB,
    )
from services.company_identity import usuario_vinculado
from services.social_oauth import SocialOAuthError, provider_config, verified_identity
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
    SocialSignupComplete,
    SocialSignupPublic,
    )

router = APIRouter(prefix="/auth", tags=["Auth"])

RESET_EXPIRATION_MINUTES = 10
RESET_MAX_ATTEMPTS = 5
OAUTH_STATE_MAX_AGE = 10 * 60
SOCIAL_SIGNUP_MAX_AGE = 15 * 60
SOCIAL_SIGNUP_COOKIE = "coroa_social_signup"


def _genero_banco(value: str | None):
    if not value:
        return None
    return {
        "Masculino": "masculino",
        "Feminino": "feminino",
        "Prefiro não informar": "nao_informado",
    }.get(value, value.strip()[:15])

def clear_sessions(request, db):
    cookie = request.cookies.get(COOKIE_NAME)
    if cookie:
        for model in (AuthSessionDB, MentorSessionDB):
            session = db.get(model, token_hash(cookie))
            if session:
                db.delete(session)


def _set_entrepreneur_session(request: Request, response: Response, db: Session, user: EmpreendedorDB):
    clear_sessions(request, db)
    token = secrets.token_urlsafe(32)
    db.add(AuthSessionDB(
        token_hash=token_hash(token),
        id_empreendedor=user.id_empreendedor,
        expires_at=datetime.utcnow() + timedelta(hours=8),
    ))
    db.commit()
    settings = get_settings()
    response.set_cookie(
        COOKIE_NAME, token, max_age=8 * 3600, httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite, path="/",
    )
    response.headers["Cache-Control"] = "no-store"


def _oauth_redirect(reason: str = "success") -> RedirectResponse:
    settings = get_settings()
    return RedirectResponse(f"{settings.frontend_origin}/login?oauth={reason}", status_code=303)


def _social_signup_redirect(provider: str) -> RedirectResponse:
    return RedirectResponse(
        f"{get_settings().frontend_origin}/cadastro-empreendedor?social={provider}",
        status_code=303,
    )


def _social_signup(request: Request, db: Session) -> SocialSignupDB:
    token = request.cookies.get(SOCIAL_SIGNUP_COOKIE, "")
    signup = db.get(SocialSignupDB, token_hash(token)) if token else None
    if not signup or signup.expires_at < datetime.utcnow():
        if signup:
            db.delete(signup)
            db.commit()
        raise HTTPException(401, "Seu cadastro social expirou. Comece novamente pela tela de login.")
    return signup


@router.get("/oauth/{provider}")
def iniciar_oauth(provider: str):
    try:
        oauth = provider_config(provider, get_settings())
    except SocialOAuthError as exc:
        raise HTTPException(503, str(exc)) from exc
    state = secrets.token_urlsafe(32)
    response = RedirectResponse(oauth.authorization_url_for(state), status_code=303)
    response.set_cookie(
        f"coroa_oauth_{provider}", state, max_age=OAUTH_STATE_MAX_AGE,
        httponly=True, secure=get_settings().session_cookie_secure,
        samesite="lax", path=f"/auth/oauth/{provider}/callback",
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/oauth/{provider}/callback")
async def callback_oauth(
    provider: str,
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    cookie_name = f"coroa_oauth_{provider}"
    expected_state = request.cookies.get(cookie_name)
    if error:
        response = _oauth_redirect("cancelled")
    elif not code or not state or not expected_state or not secrets.compare_digest(state, expected_state):
        response = _oauth_redirect("invalid_state")
    else:
        try:
            oauth = provider_config(provider, get_settings())
            identity = await verified_identity(oauth, code)
            user = db.query(EmpreendedorDB).filter(func.lower(EmpreendedorDB.email) == identity.email).first()
            if not user:
                signup_token = secrets.token_urlsafe(32)
                db.add(SocialSignupDB(
                    token_hash=token_hash(signup_token), provider=provider,
                    email=identity.email, nome=identity.name,
                    expires_at=datetime.utcnow() + timedelta(seconds=SOCIAL_SIGNUP_MAX_AGE),
                ))
                db.commit()
                response = _social_signup_redirect(provider)
                response.set_cookie(
                    SOCIAL_SIGNUP_COOKIE, signup_token, max_age=SOCIAL_SIGNUP_MAX_AGE,
                    httponly=True, secure=get_settings().session_cookie_secure,
                    samesite=get_settings().session_cookie_samesite, path="/",
                )
            else:
                response = _oauth_redirect()
                _set_entrepreneur_session(request, response, db, user)
        except SocialOAuthError:
            response = _oauth_redirect("provider_error")
    response.delete_cookie(
        cookie_name, path=f"/auth/oauth/{provider}/callback",
        secure=get_settings().session_cookie_secure, httponly=True, samesite="lax",
    )
    return response


@router.get("/social-signup", response_model=SocialSignupPublic)
def obter_cadastro_social(request: Request, db: Session = Depends(get_db)):
    signup = _social_signup(request, db)
    return SocialSignupPublic(provider=signup.provider, nome=signup.nome, email=signup.email)


@router.post("/social-signup", status_code=201, dependencies=[Depends(validate_origin)])
def concluir_cadastro_social(
    dados: SocialSignupComplete,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    signup = _social_signup(request, db)
    if db.query(EmpreendedorDB).filter(func.lower(EmpreendedorDB.email) == signup.email).first():
        raise HTTPException(409, "Já existe uma conta com esse e-mail. Volte ao login.")

    user = EmpreendedorDB(
        nome=signup.nome,
        email=signup.email,
        senha=hash_password(secrets.token_urlsafe(48)),
        telefone=dados.telefone.strip(),
        cpf=dados.cpf.strip() if dados.cpf else None,
        genero=_genero_banco(dados.genero),
        data_nascimento=dados.data_nascimento,
    )
    db.add(user)
    db.delete(signup)
    try:
        db.flush()
        _set_entrepreneur_session(request, response, db, user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Já existe uma conta com esse e-mail.") from None
    response.delete_cookie(
        SOCIAL_SIGNUP_COOKIE, path="/", secure=get_settings().session_cookie_secure,
        httponly=True, samesite=get_settings().session_cookie_samesite,
    )
    return {"message": "Conta criada com sucesso.", "Empreendedor": EmpreendedorPublic.model_validate(user)}


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

    _set_entrepreneur_session(request, response, db, user)

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
