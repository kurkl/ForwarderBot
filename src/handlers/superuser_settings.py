from aiogram.types import Message, CallbackQuery
from aiogram.types.chat import ChatType
from aiogram.utils.callback_data import CallbackData

from src.runner import dp
from src.utils.keyboards import InlineConstructor, DefaultConstructor
from src.database.entities import Chat, User, VkPostData

cb_admin_settings = CallbackData("admin", "property", "value")

markup = DefaultConstructor.create_kb(
    [{"text": "Веб-панель"}, {"text": "Активные сессии"}, {"text": "Статистика"}],
    [2, 1],
)


# inline_markup = InlineConstructor.create_kb([{}], [])


@dp.message_handler(chat_type=ChatType.PRIVATE, commands=["admin"], is_superuser=True)
async def admin_settings_handler(message: Message):
    await message.answer(f"Текущий админ: {message.from_user.username}", reply_markup=markup)


@dp.callback_query_handler(cb_admin_settings.filter(property="group_manager_state", value="change"))
async def admin_settings_add_groups(query: CallbackQuery, cd_data: dict, chat: Chat = None):
    pass
