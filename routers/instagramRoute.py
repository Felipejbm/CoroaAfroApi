from datetime import datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import APIRouter, Depends, HTTPException, Query
import hmac
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from config import Settings, get_settings
from database import get_db
from models import AuthSessionDB, EmpreendedorDB, MetaInstagramConnectionDB
from dependencies import get_current_user, get_auth_session, token_hash
from services.meta_graph import MetaGraphError, MetaGraphService


router = APIRouter(tags=["Instagram"])


def authenticated_instagram_id(
    empreendedor_id: int | None = Query(default=None, gt=0),
    user: EmpreendedorDB = Depends(get_current_user),
) -> int:
    if empreendedor_id is not None and empreendedor_id != user.id_empreendedor:
        raise HTTPException(403, "Você não pode acessar a conexão de outro usuário.")
    return user.id_empreendedor


def _service(settings: Settings) -> MetaGraphService:
    try:
        return MetaGraphService(settings)
    except MetaGraphError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


def _connection(
    empreendedor_id: int,
    db: Session,
) -> tuple[MetaInstagramConnectionDB, MetaGraphService, str]:
    service = _service(get_settings())
    connection = db.query(MetaInstagramConnectionDB).filter(
        MetaInstagramConnectionDB.id_empreendedor == empreendedor_id
    ).first()
    if not connection:
        raise HTTPException(
            status_code=404,
            detail="Instagram ainda não conectado para este empreendedor.",
        )
    if connection.token_expires_at and connection.token_expires_at <= datetime.utcnow():
        raise HTTPException(
            status_code=401,
            detail="A autorização da Meta expirou. Conecte o Instagram novamente.",
        )
    try:
        token = service.decrypt_token(connection.access_token_encrypted)
    except MetaGraphError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return connection, service, token


async def _graph_call(awaitable: Any) -> dict[str, Any]:
    try:
        return _sanitize_meta_response(await awaitable)
    except MetaGraphError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


def _sanitize_meta_response(value: Any) -> Any:
    """Remove segredos que a Meta inclui em campos e URLs de paginação."""
    secret_keys = {"access_token", "appsecret_proof"}
    if isinstance(value, dict):
        return {
            key: _sanitize_meta_response(item)
            for key, item in value.items()
            if key.lower() not in secret_keys
        }
    if isinstance(value, list):
        return [_sanitize_meta_response(item) for item in value]
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        parts = urlsplit(value)
        safe_query = [
            (key, item)
            for key, item in parse_qsl(parts.query, keep_blank_values=True)
            if key.lower() not in secret_keys
        ]
        return urlunsplit(
            (parts.scheme, parts.netloc, parts.path, urlencode(safe_query), parts.fragment)
        )
    return value


@router.get("/auth/meta", summary="Iniciar conexão com Instagram")
def iniciar_oauth_meta(
    empreendedor_id: int = Depends(authenticated_instagram_id),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    session: AuthSessionDB = Depends(get_auth_session),
):
    empreendedor = db.query(EmpreendedorDB).filter(
        EmpreendedorDB.id_empreendedor == empreendedor_id
    ).first()
    if not empreendedor:
        raise HTTPException(status_code=404, detail="Empreendedor não encontrado.")
    url = _service(settings).authorization_url(empreendedor_id)
    state = dict(parse_qsl(urlsplit(url).query))["state"]
    session.oauth_state_hash = token_hash(state)
    db.commit()
    return RedirectResponse(url, status_code=307)


@router.get("/auth/meta/callback", summary="Callback OAuth da Meta")
async def callback_oauth_meta(
    state: str,
    code: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    session: AuthSessionDB = Depends(get_auth_session),
):
    if not session.oauth_state_hash or not hmac.compare_digest(session.oauth_state_hash, token_hash(state)):
        raise HTTPException(400, "Autorização inválida ou já utilizada. Inicie novamente.")
    session.oauth_state_hash = None
    db.commit()
    if error:
        raise HTTPException(
            status_code=400,
            detail=error_description or "A autorização da Meta foi cancelada.",
        )
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code não recebido.")

    service = _service(settings)
    try:
        empreendedor_id = service.read_state(state)
        if empreendedor_id != session.id_empreendedor:
            raise MetaGraphError("Autorização não pertence ao usuário conectado.", 403)
        user_token, expires_at = await service.exchange_code(code)
        accounts = await service.discover_instagram_accounts(user_token)
    except MetaGraphError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    empreendedor = db.query(EmpreendedorDB).filter(
        EmpreendedorDB.id_empreendedor == empreendedor_id
    ).first()
    if not empreendedor:
        raise HTTPException(status_code=404, detail="Empreendedor não encontrado.")
    if not accounts:
        raise HTTPException(
            status_code=400,
            detail=(
                "Nenhuma Página autorizada possui uma conta profissional do "
                "Instagram vinculada."
            ),
        )

    selected = accounts[0]
    connection = db.query(MetaInstagramConnectionDB).filter(
        MetaInstagramConnectionDB.id_empreendedor == empreendedor_id
    ).first()
    if not connection:
        connection = MetaInstagramConnectionDB(id_empreendedor=empreendedor_id)
        db.add(connection)

    connection.facebook_page_id = selected["facebook_page_id"]
    connection.facebook_page_name = selected["facebook_page_name"]
    connection.instagram_business_account_id = selected["instagram_business_account_id"]
    connection.access_token_encrypted = service.encrypt_token(selected["page_access_token"])
    connection.token_expires_at = expires_at
    db.commit()

    if settings.meta_success_redirect_url:
        return RedirectResponse(settings.meta_success_redirect_url, status_code=303)
    return {
        "message": "Instagram conectado com sucesso.",
        "connection": {
            "empreendedor_id": empreendedor_id,
            "facebook_page_id": selected["facebook_page_id"],
            "facebook_page_name": selected["facebook_page_name"],
            "instagram_business_account_id": selected["instagram_business_account_id"],
            "instagram_username": selected["instagram_username"],
        },
        "authorized_instagram_accounts": len(accounts),
    }


@router.get("/instagram/profile", summary="Obter perfil profissional do Instagram")
async def obter_perfil_instagram(
    empreendedor_id: int = Depends(authenticated_instagram_id),
    db: Session = Depends(get_db),
):
    connection, service, token = _connection(empreendedor_id, db)
    return await _graph_call(
        service.graph_get(
            f"/{connection.instagram_business_account_id}",
            token,
            fields="id,username,name,profile_picture_url,followers_count,media_count",
        )
    )


@router.get("/instagram/media", summary="Listar mídias do Instagram")
async def listar_midias_instagram(
    empreendedor_id: int = Depends(authenticated_instagram_id),
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    connection, service, token = _connection(empreendedor_id, db)
    return await _graph_call(
        service.graph_get(
            f"/{connection.instagram_business_account_id}/media",
            token,
            fields=(
                "id,caption,media_type,media_product_type,media_url,thumbnail_url,"
                "permalink,timestamp,like_count,comments_count"
            ),
            limit=limit,
        )
    )


@router.get("/instagram/insights", summary="Obter insights da conta do Instagram")
async def obter_insights_conta(
    empreendedor_id: int = Depends(authenticated_instagram_id),
    metric: str = Query(default="reach", pattern=r"^[a-z_]+(,[a-z_]+)*$"),
    period: str = Query(default="day", pattern=r"^(day|week|days_28|lifetime)$"),
    since: str | None = None,
    until: str | None = None,
    db: Session = Depends(get_db),
):
    connection, service, token = _connection(empreendedor_id, db)
    params: dict[str, Any] = {"metric": metric, "period": period}
    if since:
        params["since"] = since
    if until:
        params["until"] = until
    return await _graph_call(
        service.graph_get(
            f"/{connection.instagram_business_account_id}/insights",
            token,
            **params,
        )
    )


@router.get(
    "/instagram/media/{media_id}/insights",
    summary="Obter insights de uma mídia do Instagram",
)
async def obter_insights_midia(
    media_id: str,
    empreendedor_id: int = Depends(authenticated_instagram_id),
    metric: str = Query(
        default="reach,likes,comments,saved,shares",
        pattern=r"^[a-z_]+(,[a-z_]+)*$",
    ),
    db: Session = Depends(get_db),
):
    if not media_id.isdigit():
        raise HTTPException(status_code=400, detail="ID de mídia inválido.")
    connection, service, token = _connection(empreendedor_id, db)
    media = await _graph_call(
        service.graph_get(f"/{media_id}", token, fields="id,owner")
    )
    if media.get("owner", {}).get("id") != connection.instagram_business_account_id:
        raise HTTPException(status_code=403, detail="A mídia não pertence à conta conectada.")
    return await _graph_call(
        service.graph_get(f"/{media_id}/insights", token, metric=metric)
    )
