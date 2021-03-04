from loguru import logger
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import Executor
from aiogram.contrib.fsm_storage.redis import RedisStorage2

from src.filters import filters_setup
from src.settings import (
    REDIS_HOST,
    REDIS_PORT,
    WEBHOOK_URL,
    REDIS_DB_FSM,
    TG_BOT_TOKEN,
    WEBHOOK_PATH,
    REDIS_PASSWORD,
    BOT_PUBLIC_PORT,
)

bot = Bot(token=TG_BOT_TOKEN, parse_mode=types.ParseMode.HTML, validate_token=True)
storage = RedisStorage2(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB_FSM)
dp = Dispatcher(bot=bot, storage=storage)
runner = Executor(dp, skip_updates=True)


async def on_startup_webhook(dispatcher: Dispatcher):
    logger.info("Configure Web-Hook URL to: {url}", url=WEBHOOK_URL)
    await dispatcher.bot.set_webhook(WEBHOOK_URL)


def run_bot():
    from src.middleware import middlewares_setup
    from src.database.db import db_setup
    from src.utils.logging import logging_setup
    from src.utils.scheduler import scheduler_setup
    from src.services.vk.public import vk_scheduler_setup

    logging_setup()
    db_setup(runner)
    scheduler_setup(runner)
    vk_scheduler_setup(runner)
    middlewares_setup(dp)
    filters_setup(dp)
    # noinspection PyUnresolvedReferences
    import src.handlers

    runner.on_startup(on_startup_webhook, webhook=True, polling=False)
    runner.start_webhook(webhook_path=WEBHOOK_PATH, port=BOT_PUBLIC_PORT)
