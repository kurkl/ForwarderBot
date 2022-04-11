from datetime import datetime

from loguru import logger
from aiogram import Dispatcher, types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from src.database.schemas import UserCreate
from src.database.repositories import UserRepository, get_repository


class ACLMiddleware(BaseMiddleware):
    async def setup_chat(self, data: dict, tg_user: types.User):
        if tg_user.first_name == "Telegram":
            return
        user_repo = get_repository(UserRepository, self.manager.bot["engine"])
        user_id = tg_user.id
        user = await user_repo.get_object(filters={"telegram_id": user_id})
        if not user:
            user = await user_repo.create(UserCreate(telegram_id=user_id))

        data["user"] = user

    async def on_pre_process_message(self, message: types.Message, data: dict):
        await self.setup_chat(data, message.from_user)

    async def on_pre_process_callback_query(self, query: types.CallbackQuery, data: dict):
        await self.setup_chat(data, query.from_user)


def middlewares_setup(dispatcher: Dispatcher):
    logger.info("Configure middlewares")

    dispatcher.middleware.setup(LoggingMiddleware("bot"))
    dispatcher.middleware.setup(ACLMiddleware())
