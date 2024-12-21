import secrets

from typing import NewType

from pydantic import AnyHttpUrl, AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from auction._types import UserID


LanguageCode = NewType("LanguageCode", str)


class DivarConfig(BaseSettings):
    app_slug: str
    api_key: str
    oauth_secret: str
    oauth_redirect_url: str

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="divar_", extra="allow"
    )


class Config(BaseSettings):
    debug: bool = False
    project_url: AnyHttpUrl
    secret_key: str = secrets.token_urlsafe(32)
    openapi_url: str = "/openapi.json"
    docs_url: str = "/docs"
    templates_dir_path: str = "auction/pages"
    mock_user_id: UserID
    database_url: AnyUrl

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    @property
    def database_sync_url(self) -> str:
        database_url = str(self.database_url)
        return database_url.replace("sqlite+aiosqlite", "sqlite")


config = Config()  # type: ignore
divar_config = DivarConfig()  # type: ignore
