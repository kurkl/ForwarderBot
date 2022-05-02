from typing import Any, Callable, Awaitable, cast

from aiogram import BaseMiddleware, types

from database.db import db_session
from database.schemas import UserCreateSchema
from database.repositories import UserRepository, get_repository


class ACLMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: dict[str, Any],
    ):
        event = cast(types.Message, event)
        session = data.get("session")
        user_repository = get_repository(UserRepository, session)
        user = await user_repository.get_object({"telegram_id": event.from_user.id})
        if not user:
            user = await user_repository.create_object(UserCreateSchema(telegram_id=event.from_user.id))

        data["user"] = user

        return await handler(event, data)


class DBSessionMiddleware(BaseMiddleware):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine

    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: dict[str, Any],
    ):
        async with db_session(self.engine) as session:
            data["session"] = session

            return await handler(event, data)
