from dataclasses import dataclass
from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.handler import ctx_data

from src.database.entities import User


@dataclass
class IsSuperUserFilter(BoundFilter):
    key = "is_superuser"
    is_superuser: bool

    async def check(self, obj) -> bool:
        # data = ctx_data.get()
        user = await User.get(obj.from_user.id)
        return user.is_superuser
