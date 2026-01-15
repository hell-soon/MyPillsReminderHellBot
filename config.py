from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    token: str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="BOT__",
        extra="ignore",
    )


conf = Config()
