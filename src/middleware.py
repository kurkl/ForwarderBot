from loguru import logger
from aiogram import Dispatcher, types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from src.database.entities import Chat, User


class ACLMiddleware(BaseMiddleware):
    async def setup_chat(self, data: dict, user: types.User, chat: types.Chat = None):
        user_id = user.id
        chat_id = chat.id if chat else user_id
        chat_type = chat.type if chat else "private"

        user = await User.get(user_id)
        if not user:
            user = await User.create(id=user_id)

        chat = await Chat.get(chat_id)
        if not chat:
            chat = await Chat.create(id=chat_id, type=chat_type)

        data["user"] = user
        data["chat"] = chat

    async def on_pre_process_message(self, message: types.Message, data: dict):
        await self.setup_chat(data, message.from_user, message.chat)

    async def on_pre_process_callback_query(self, query: types.CallbackQuery, data: dict):
        await self.setup_chat(data, query.from_user, query.message.chat if query.message else None)


def middlewares_setup(dispatcher: Dispatcher):
    logger.info("Configure middlewares")

    dispatcher.middleware.setup(LoggingMiddleware("bot"))
    dispatcher.middleware.setup(ACLMiddleware())
