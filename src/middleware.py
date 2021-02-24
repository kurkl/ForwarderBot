from loguru import logger
from aiogram import Dispatcher, types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from src.database.crud import customer
from src.database.schemas import UserCreate


class ACLMiddleware(BaseMiddleware):
    async def setup_chat(self, data: dict, user: types.User):
        user_id = user.id

        user = await customer.get(user_id)
        if not user:
            user = await customer.create(UserCreate(telegram_id=user_id))

        data["user"] = user

    async def on_pre_process_message(self, message: types.Message, data: dict):
        await self.setup_chat(data, message.from_user)

    async def on_pre_process_callback_query(self, query: types.CallbackQuery, data: dict):
        await self.setup_chat(data, query.from_user)


def middlewares_setup(dispatcher: Dispatcher):
    logger.info("Configure middlewares")

    dispatcher.middleware.setup(LoggingMiddleware("bot"))
    dispatcher.middleware.setup(ACLMiddleware())
