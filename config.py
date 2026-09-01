from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://root:@localhost/coroa_afro"

    meta_app_id: str | None = None
    meta_app_secret: str | None = None
    meta_redirect_uri: str | None = None
    meta_token_encryption_key: str | None = None
    meta_graph_api_version: str = "v26.0"
    meta_success_redirect_url: str | None = None
    frontend_origin: str = "http://localhost:5173"
    session_cookie_secure: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
