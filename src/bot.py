from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import Executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from src.settings import DEBUG, TG_ME, VK_WALL_ID, LOG_CHANNEL, TG_BOT_TOKEN, TARGET_CHANNEL
from src.database.db import db_setup
from src.utils.logging import logging_setup
from src.services.vk_parser import VkParserBroadcaster

storage = MemoryStorage()
bot = Bot(token=TG_BOT_TOKEN, parse_mode=types.ParseMode.HTML, validate_token=True)
dp = Dispatcher(bot=bot, storage=storage)
runner = Executor(dp, skip_updates=True)
broadcaster = VkParserBroadcaster(bot, VK_WALL_ID, [TARGET_CHANNEL], LOG_CHANNEL, TG_ME)


def run_bot_polling():
    logging_setup()
    db_setup(runner)
    import src.handlers

    if DEBUG:
        runner.start_polling()
