from loguru import logger
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hlink
from aiogram.dispatcher.filters import CommandHelp, CommandStart
from aiogram.utils.callback_data import CallbackData

from src.runner import dp
from src.utils.keyboards import InlineConstructor
from src.database.entities import User

base_user_cb = CallbackData("level", "action")


@dp.message_handler(commands=["service"])
async def cb_base_user_actions(message: Message):
    markup = InlineConstructor.create_kb(
        [
            {"text": "Задать стены", "cb": ({"action": "add"}, base_user_cb)},
            {"text": "Список стен", "cb": ({"action": "view"}, base_user_cb)},
            {"text": "Начать репосты", "cb": ({"action": "start"}, base_user_cb)},
            {"text": "Пауза", "cb": ({"action": "stop"}, base_user_cb)},
            {"text": "Статус", "cb": ({"action": "status"}, base_user_cb)},
        ],
        [2, 1, 2],
    )
    await message.reply("Меню", reply_markup=markup)


@dp.callback_query_handler(base_user_cb.filter(action=["start", "stop"]))
async def cb_user_service_state(query: CallbackQuery, user: User, callback_data: dict):
    logger.info(callback_data)
    await query.answer()


@dp.callback_query_handler(base_user_cb.filter(action="done"))
async def user_settings_done(query: CallbackQuery):
    await query.answer("Подтверждено!", show_alert=True)
    await query.message.delete()
