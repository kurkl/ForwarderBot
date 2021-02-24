import os
import pathlib

from environs import Env
from alembic.config import Config

env = Env()
env.read_env()

PROJECT_PATH = pathlib.Path(__file__).parent.parent.resolve()

DEBUG = True
# vk settings
VK_TOKEN = env.str("VK_TOKEN")
VK_WALL_ID = env.int("VK_WALL_ID")
# telegram settings
TARGET_CHANNEL = env.int("TARGET_CHANNEL")
TEST_CHANNEL = env.int("TEST_CHANNEL", 0)
CHAT_GROUP = env.int("CHAT_GROUP", 0)
TG_BOT_TOKEN = env.str("TG_BOT_TOKEN")
TG_ME = env.int("TG_ME")
LOG_CHANNEL = env.int("LOG_CHANNEL", TG_ME)
# postgres settings
POSTGRES_HOST = env.str("POSTGRES_HOST", "localhost")
POSTGRES_PORT = env.int("POSTGRES_PORT", 5432)
POSTGRES_PASSWORD = env.str("POSTGRES_PASSWORD" "")
POSTGRES_USER = env.str("POSTGRES_USER", "postgres")
POSTGRES_DB = env.str("POSTGRES_DB", "postgres")
POSTGRES_URI = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
# redis
REDIS_HOST = env.str("REDIS_HOST", "localhost")
REDIS_PORT = env.int("REDIS_PORT", 6379)
REDIS_DB_FSM = env.int("REDIS_DB_FSM", 0)
REDIS_PASSWORD = env.str("REDIS_PASSWORD")


def make_alembic_config(cmd_opts, base_path: str = PROJECT_PATH) -> Config:
    # Replace path to alembic.ini file to absolute
    if not os.path.isabs(cmd_opts.config):
        cmd_opts.config = os.path.join(base_path, cmd_opts.config)

    config = Config(file_=cmd_opts.config, ini_section=cmd_opts.name, cmd_opts=cmd_opts)

    # Replace path to alembic folder to absolute
    alembic_location = config.get_main_option("script_location")
    if not os.path.isabs(alembic_location):
        config.set_main_option("script_location", os.path.join(base_path, alembic_location))
    if cmd_opts.pg_url:
        config.set_main_option("sqlalchemy.url", cmd_opts.pg_url)

    return config
