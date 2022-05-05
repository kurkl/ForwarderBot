from aiogram import types
from aiogram.dispatcher.filters import BaseFilter


class IsSuperUserFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        pass
