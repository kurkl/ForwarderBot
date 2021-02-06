from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import Executor

from src.filters import filters_setup
from src.settings import DEBUG, TG_BOT_TOKEN
from src.database.db import db_setup
from src.utils.logging import logging_setup

bot = Bot(token=TG_BOT_TOKEN, parse_mode=types.ParseMode.HTML, validate_token=True)
dp = Dispatcher(bot=bot)
runner = Executor(dp, skip_updates=True)


def run_bot():
    logging_setup()
    db_setup(runner)
    filters_setup(dp)
    # noinspection PyUnresolvedReferences
    import src.handlers

    if DEBUG:
        runner.start_polling()
