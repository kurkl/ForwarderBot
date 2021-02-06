from loguru import logger
from aiogram import Dispatcher
from aiogram.utils.executor import Executor

from src.settings import TG_ME, POSTGRES_URI

from .entities import User, db


async def on_startup(dispatcher: Dispatcher):
    logger.info("Setup PostgreSQL Connection")
    await db.set_bind(POSTGRES_URI)
    await User.create_superuser(TG_ME)


async def on_shutdown(dispatcher: Dispatcher):
    bind = db.pop_bind()
    if bind:
        logger.info("Close PostgreSQL Connection")
        await bind.close()


def db_setup(executor: Executor):
    executor.on_startup(on_startup)
    executor.on_shutdown(on_shutdown)
