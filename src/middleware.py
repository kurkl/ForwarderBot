from loguru import logger
from aiogram import Dispatcher, types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from src.database import crud, schemas


class ACLMiddleware(BaseMiddleware):
    async def setup_chat(self, data: dict, tg_user: types.User):
        user_id = tg_user.id

        user = await crud.user.get(user_id)
        if not user:
            user = await crud.user.create(schemas.UserCreate(telegram_id=user_id))

        subscriber = await crud.subscriber.get(user.id)

        if not subscriber:
            subscriber = await crud.subscriber.create(schemas.SubscriberCreate(subscriber_id=user.id))

        targets = await crud.target.get(subscriber.id)

        if not targets:
            await crud.target.create(schemas.TargetCreate(subscriber_id=subscriber.id))

        data["user"], data["subscriber"] = user, subscriber

    async def on_pre_process_message(self, message: types.Message, data: dict):
        await self.setup_chat(data, message.from_user)

    async def on_pre_process_callback_query(self, query: types.CallbackQuery, data: dict):
        await self.setup_chat(data, query.from_user)


def middlewares_setup(dispatcher: Dispatcher):
    logger.info("Configure middlewares")

    dispatcher.middleware.setup(LoggingMiddleware("bot"))
    dispatcher.middleware.setup(ACLMiddleware())
