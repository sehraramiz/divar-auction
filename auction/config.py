from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


config = Config()  # type: ignore
divar_config = DivarConfig()  # type: ignore
