from enum import Enum
from typing import Type
from functools import lru_cache

from pydantic import RedisDsn, PostgresDsn, BaseSettings, validator


class AppEnvironments(Enum):
    prod: str = "prod"
    dev: str = "dev"
    local: str = "dev"


class BaseAppConfig(BaseSettings):
    app_env: AppEnvironments = AppEnvironments.local

    class Config:
        case_sensitive = True
        env_file = ".env.dev"


class AppConfig(BaseAppConfig):
    # Common
    DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
    DOMAIN: str
    BOT_PUBLIC_PORT: int = 8080
    I18N_DOMAIN: str = "forwarder_bot"
    LOCALES_DIR: str = ""
    # vk settings
    VK_TOKEN: str
    # telegram settings
    TG_BOT_TOKEN: str
    WEBHOOK_PATH: str = "/webhook"
    WEBHOOK_URL: str | None = None
    # postgres settings
    SQLALCHEMY_DB_URI: PostgresDsn
    # redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB_FSM: int = 0
    REDIS_DB_JOBS: int = 0
    REDIS_DB_CACHE: int = 2
    REDIS_URI: RedisDsn | None = None

    @validator("REDIS_URI", pre=True, allow_reuse=True)
    def assemble_redis_uri(cls, v: str | None, values: dict) -> str:
        if isinstance(v, str):
            return v

        return RedisDsn.build(
            scheme="redis",
            password=values.get("REDIS_PASSWORD"),
            host=values.get("REDIS_HOST"),
            port=values.get("REDIS_PORT"),
        )

    @validator("WEBHOOK_URL", pre=True, allow_reuse=True)
    def assemble_webhook_url(cls, v: str | None, values: dict) -> str:
        if isinstance(v, str):
            return v

        return f"{values.get('DOMAIN')}{values.get('WEBHOOK_PATH')}"


class DevAppConfig(AppConfig):
    pass


class LocalAppConfig(AppConfig):
    class Config(AppConfig.Config):
        env_file = "../.env.dev"


class ProdAppConfig(AppConfig):
    class Config(AppConfig.Config):
        env_file = ".env.prod"


environments: dict[AppEnvironments, Type[AppConfig]] = {
    AppEnvironments.dev: DevAppConfig,
    AppEnvironments.prod: ProdAppConfig,
    AppEnvironments.local: LocalAppConfig,
}


@lru_cache()
def get_app_config() -> AppConfig:
    app_env = BaseAppConfig().app_env
    config = environments[app_env]

    return config()


setting = get_app_config()
