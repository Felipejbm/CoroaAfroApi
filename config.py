from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://root:@localhost:3306/coroa_afro"

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5"
    openai_timeout_seconds: float = 30.0
    openai_max_output_tokens: int = 2000

    meta_app_id: str | None = None
    meta_app_secret: str | None = None
    meta_redirect_uri: str | None = None
    meta_token_encryption_key: str | None = None
    meta_graph_api_version: str = "v26.0"
    meta_success_redirect_url: str | None = None
    google_client_id: str | None = None
    google_client_secret: SecretStr | None = None
    google_redirect_uri: str | None = None
    linkedin_client_id: str | None = None
    linkedin_client_secret: SecretStr | None = None
    linkedin_redirect_uri: str | None = None
    frontend_origin: str = "https://coroa-afro.vercel.app/"
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    session_cookie_secure: bool = False
    brevo_api_key: SecretStr | None = None
    smtp_from: str = ""
    password_reset_demo_mode: bool = False
    admin_email: str | None = None
    admin_password: SecretStr | None = None
    @field_validator("database_url")
    @classmethod
    def mysql_driver(cls, value: str) -> str:
        if value.startswith("mysql://"):
            return value.replace("mysql://", "mysql+pymysql://", 1)
        return value

    @field_validator("frontend_origin")
    @classmethod
    def normalize_origin(cls, value: str) -> str:
        from urllib.parse import urlsplit
        value = value.strip().rstrip("/")
        parts = urlsplit(value)
        if parts.scheme not in {"http", "https"} or not parts.netloc or parts.path or parts.query or parts.fragment or parts.username:
            raise ValueError("FRONTEND_ORIGIN deve conter apenas a origem HTTP(S), sem caminho.")
        return value

    @model_validator(mode="after")
    def validate_cookie(self):
        if self.session_cookie_samesite == "none" and not self.session_cookie_secure:
            raise ValueError("SESSION_COOKIE_SAMESITE=none exige SESSION_COOKIE_SECURE=true.")
        return self

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )



@lru_cache
def get_settings() -> Settings:
    return Settings()
