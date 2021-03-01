from datetime import datetime

from loguru import logger
from aiogram.types import Message
from aiogram.utils.markdown import hbold, hlink
from aiogram.dispatcher.filters import Command, CommandHelp, CommandStart

from settings import TIME_FORMAT
from src.runner import dp
from database.entities import Subscriber

from .markups.user import main_menu_kb


@dp.message_handler(CommandStart())
async def cmd_start(message: Message):
    logger.info(f"User {message.from_user.id} start conversation with bot")
    await message.answer(
        f"Привет {hbold(message.from_user.full_name)}.\nБот находится в активной разработке,\n"
        f"возможны ошибки и/или критические баги. Пожалуйста, используйте обратную связь при возникновении вопросов.\n"
        f"Начать: /service\nПомощь: /help\n"
    )


@dp.message_handler(CommandHelp())
async def cmd_help(message: Message):
    logger.info(f"User {message.from_user.id} send help command")
    await message.reply(
        f"{hbold('Список команд:')}\n/help - Увидеть это сообщение\n"
        f"/service - Главное меню\n/contacts - Обратная связь\n/status"
    )


@dp.message_handler(Command("contacts"))
async def cmd_feedback(message: Message):
    await message.reply(
        f"Связь со мной: https://t.me/kurkl\n"
        f"Репозиторий: {hlink('Github', 'https://github.com/LehaDurotar/ForwarderBot')}"
    )


@dp.message_handler(Command("status"))
async def cmd_status(message: Message):
    await message.reply("Статус")


@dp.message_handler(Command("service"))
async def cmd_user_services(message: Message, subscriber: Subscriber):
    if subscriber.expiration_dt.date() >= datetime.date(datetime.now()):
        await message.answer(
            f"Ваш уровень подписчика: {subscriber.level}\n"
            f"Активен до: {hbold(subscriber.expiration_dt.date().strftime(TIME_FORMAT))}\n"
            f"Информация о подписке: /subscribe\nПомощь: /help\nДоступные сервисы",
            reply_markup=main_menu_kb,
        )
    else:
        await message.answer("Ваша подписка неактивна, сервис недоступен :(")
