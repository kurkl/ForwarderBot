import os
from enum import Enum
from typing import Type
from functools import lru_cache
from logging.config import dictConfig

from pydantic import RedisDsn, PostgresDsn, BaseSettings, validator

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s.%(funcName)s: %(message)s"},
        "gunicorn": {"format": "%(name)s.%(funcName)s: %(message)s"},
    },
    "handlers": {
        "stdout": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "gunicorn_file": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "gunicorn",
            "filename": "logs/gunicorn.log",
            "maxBytes": 50 * 1024,
            "backupCount": 20,
        },
        "main_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "filename": "logs/main.log",
            "maxBytes": 50 * 1024,
            "backupCount": 10,
        },
    },
    "loggers": {
        "gunicorn": {
            "handlers": ["stdout", "gunicorn_file"],
            "level": "INFO",
            "propagate": True,
        },
        "root": {
            "handlers": ["stdout", "main_file"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}


def setup_logging():
    os.makedirs("logs", exist_ok=True)
    dictConfig(LOGGING_CONFIG)


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
    REDIS_PORT: str = "6379"
    REDIS_PASSWORD: str = ""
    REDIS_DB_JOBS: int = 1
    REDIS_DB_CACHE: int = 2
    REDIS_BASE_URI: RedisDsn | None = None

    @validator("REDIS_BASE_URI", pre=True, allow_reuse=True)
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


settings = get_app_config()
