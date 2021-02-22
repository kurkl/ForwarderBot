from aiogram.types import Message, CallbackQuery
from aiogram.types.chat import ChatType
from aiogram.utils.callback_data import CallbackData

from src.runner import dp
from src.utils.keyboards import Constructor

cb_admin_settings = CallbackData("admin", "property", "value")

markup = Constructor.create_default_kb(
    [{"text": "Веб-панель"}, {"text": "Активные сессии"}, {"text": "Статистика"}],
    [2, 1],
)


@dp.message_handler(chat_type=ChatType.PRIVATE, commands=["admin"], is_superuser=True)
async def admin_settings_handler(message: Message):
    await message.answer(f"Текущий админ: {message.from_user.username}", reply_markup=markup)


