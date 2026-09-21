from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from config import Settings


class SocialOAuthError(Exception):
    pass


@dataclass(frozen=True)
class OAuthIdentity:
    email: str
    name: str


@dataclass(frozen=True)
class OAuthProvider:
    name: str
    client_id: str
    client_secret: str
    redirect_uri: str
    authorization_url: str
    token_url: str
    userinfo_url: str

    def authorization_url_for(self, state: str) -> str:
        return f"{self.authorization_url}?{urlencode({
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': 'openid profile email',
            'state': state,
        })}"


def provider_config(name: str, settings: Settings) -> OAuthProvider:
    if name == "google":
        values = (settings.google_client_id, settings.google_client_secret, settings.google_redirect_uri)
        endpoints = (
            "https://accounts.google.com/o/oauth2/v2/auth",
            "https://oauth2.googleapis.com/token",
            "https://openidconnect.googleapis.com/v1/userinfo",
        )
    elif name == "linkedin":
        values = (settings.linkedin_client_id, settings.linkedin_client_secret, settings.linkedin_redirect_uri)
        endpoints = (
            "https://www.linkedin.com/oauth/v2/authorization",
            "https://www.linkedin.com/oauth/v2/accessToken",
            "https://api.linkedin.com/v2/userinfo",
        )
    else:
        raise SocialOAuthError("Provedor de login não reconhecido.")

    client_id, secret, redirect_uri = values
    if not client_id or not secret or not secret.get_secret_value().strip() or not redirect_uri:
        raise SocialOAuthError(f"Login com {name.title()} ainda não foi configurado.")
    return OAuthProvider(name, client_id.strip(), secret.get_secret_value().strip(), redirect_uri.strip(), *endpoints)


async def verified_identity(provider: OAuthProvider, code: str) -> OAuthIdentity:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_response = await client.post(provider.token_url, data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": provider.client_id,
                "client_secret": provider.client_secret,
                "redirect_uri": provider.redirect_uri,
            }, headers={"Accept": "application/json"})
            token_response.raise_for_status()
            access_token = token_response.json().get("access_token")
            if not access_token:
                raise SocialOAuthError("O provedor não devolveu um token de acesso.")

            user_response = await client.get(
                provider.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            )
            user_response.raise_for_status()
            user = user_response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise SocialOAuthError("Não foi possível confirmar sua conta no provedor.") from exc

    email = user.get("email")
    if not isinstance(email, str) or not email.strip() or user.get("email_verified") is not True:
        raise SocialOAuthError("O provedor não disponibilizou um e-mail verificado.")
    normalized_email = email.strip().lower()
    name = user.get("name")
    if not isinstance(name, str) or not name.strip():
        name = normalized_email.split("@", 1)[0]
    return OAuthIdentity(normalized_email, name.strip()[:255])
