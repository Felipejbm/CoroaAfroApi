import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet, InvalidToken
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import Settings


class MetaGraphError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class MetaGraphService:
    AUTH_BASE_URL = "https://www.facebook.com"
    GRAPH_BASE_URL = "https://graph.facebook.com"
    OAUTH_STATE_MAX_AGE_SECONDS = 600
    SCOPES = (
        "pages_show_list",
        "pages_read_engagement",
        "business_management",
        "instagram_basic",
        "instagram_manage_insights",
    )

    def __init__(self, settings: Settings):
        missing = [
            name
            for name in (
                "meta_app_id",
                "meta_app_secret",
                "meta_redirect_uri",
                "meta_token_encryption_key",
            )
            if not getattr(settings, name)
        ]
        if missing:
            raise MetaGraphError(
                "Integração Meta não configurada. Variáveis ausentes: "
                + ", ".join(name.upper() for name in missing),
                503,
            )
        self.settings = settings
        self.version = settings.meta_graph_api_version.strip("/")
        self._state_serializer = URLSafeTimedSerializer(
            settings.meta_app_secret,
            salt="meta-oauth-state",
        )
        encryption_key = hashlib.sha256(
            settings.meta_token_encryption_key.encode("utf-8")
        ).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(encryption_key))

    def authorization_url(self, empreendedor_id: int) -> str:
        state = self._state_serializer.dumps({
            "empreendedor_id": empreendedor_id, "nonce": secrets.token_urlsafe(32),
        })
        query = urlencode(
            {
                "client_id": self.settings.meta_app_id,
                "redirect_uri": self.settings.meta_redirect_uri,
                "state": state,
                "scope": ",".join(self.SCOPES),
                "response_type": "code",
            }
        )
        return f"{self.AUTH_BASE_URL}/{self.version}/dialog/oauth?{query}"

    def read_state(self, state: str) -> int:
        try:
            payload = self._state_serializer.loads(
                state,
                max_age=self.OAUTH_STATE_MAX_AGE_SECONDS,
            )
            return int(payload["empreendedor_id"])
        except SignatureExpired as exc:
            raise MetaGraphError("A autorização expirou. Inicie a conexão novamente.", 400) from exc
        except (BadSignature, KeyError, TypeError, ValueError) as exc:
            raise MetaGraphError("Estado OAuth inválido.", 400) from exc

    def encrypt_token(self, token: str) -> str:
        return self._fernet.encrypt(token.encode("utf-8")).decode("utf-8")

    def decrypt_token(self, encrypted_token: str) -> str:
        try:
            return self._fernet.decrypt(encrypted_token.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise MetaGraphError("Não foi possível acessar o token salvo.", 500) from exc

    async def exchange_code(self, code: str) -> tuple[str, datetime | None]:
        short_lived = await self._request(
            "GET",
            "/oauth/access_token",
            params={
                "client_id": self.settings.meta_app_id,
                "client_secret": self.settings.meta_app_secret,
                "redirect_uri": self.settings.meta_redirect_uri,
                "code": code,
            },
            add_appsecret_proof=False,
        )
        short_token = short_lived.get("access_token")
        if not short_token:
            raise MetaGraphError("A Meta não retornou um access token.")

        long_lived = await self._request(
            "GET",
            "/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": self.settings.meta_app_id,
                "client_secret": self.settings.meta_app_secret,
                "fb_exchange_token": short_token,
            },
            add_appsecret_proof=False,
        )
        token = long_lived.get("access_token", short_token)
        expires_in = long_lived.get("expires_in") or short_lived.get("expires_in")
        expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in)) if expires_in else None
        return token, expires_at

    async def discover_instagram_accounts(self, user_token: str) -> list[dict[str, Any]]:
        response = await self.graph_get(
            "/me/accounts",
            user_token,
            fields="id,name,access_token,instagram_business_account{id,username}",
        )
        accounts = []
        for page in response.get("data", []):
            instagram = page.get("instagram_business_account")
            page_token = page.get("access_token")
            if instagram and page_token:
                accounts.append(
                    {
                        "facebook_page_id": page["id"],
                        "facebook_page_name": page.get("name", ""),
                        "instagram_business_account_id": instagram["id"],
                        "instagram_username": instagram.get("username"),
                        "page_access_token": page_token,
                    }
                )
        return accounts

    async def graph_get(self, path: str, token: str, **params: Any) -> dict[str, Any]:
        return await self._request(
            "GET",
            path,
            params={**params, "access_token": token},
            token=token,
        )

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any],
        token: str | None = None,
        add_appsecret_proof: bool = True,
    ) -> dict[str, Any]:
        if token and add_appsecret_proof:
            params["appsecret_proof"] = hmac.new(
                self.settings.meta_app_secret.encode("utf-8"),
                token.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

        if path.startswith("/oauth/"):
            url = f"{self.GRAPH_BASE_URL}/{self.version}{path}"
        else:
            url = f"{self.GRAPH_BASE_URL}/{self.version}/{path.lstrip('/')}"

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.request(method, url, params=params)
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise MetaGraphError("Falha de comunicação com a Meta Graph API.") from exc

        if response.is_error or "error" in payload:
            error = payload.get("error", {})
            message = error.get("message", "A Meta Graph API recusou a solicitação.")
            raise MetaGraphError(message, 400 if response.status_code < 500 else 502)
        return payload
