import secrets

from typing import NewType

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    secret_key: str = secrets.token_urlsafe(32)
    openapi_url: str = "/openapi.json"
    docs_url: str = "/docs"
    templates_dir_path: str = "auction/pages"
    supported_languages: list[LanguageCode] = [LanguageCode("fa"), LanguageCode("en")]

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


config = Config()  # type: ignore
divar_config = DivarConfig()  # type: ignore
