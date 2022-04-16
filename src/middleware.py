from typing import Any, Callable, Awaitable

from aiogram import BaseMiddleware, types

from database.db import db_session


class ACLMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: dict[str, Any],
    ):
        pass


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
