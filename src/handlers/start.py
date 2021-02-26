from loguru import logger
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.dispatcher.filters import CommandHelp, CommandStart

from src.runner import dp


@dp.message_handler(CommandStart())
async def cmd_start(message: Message):
    logger.info(f"User {message.from_user.id} start conversation with bot")
    await message.answer(
        f"Привет {hbold(message.from_user.full_name)}.\n"
        f"Чтобы начать, используй: /service\nПомощь: /help\n"
    )


@dp.message_handler(CommandHelp())
async def cmd_help(message: Message):
    logger.info(f"User {message.from_user.id} send help command")
    await message.reply(
        f"{hbold('Список команд:')}\n/help - Увидеть это сообщение\n" f"/service - Основной функционал\n"
    )
