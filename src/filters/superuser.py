from dataclasses import dataclass

from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.handler import ctx_data

from src.database.crud import customer


@dataclass
class IsSuperUserFilter(BoundFilter):
    """"""

    key = "is_superuser"
    is_superuser: bool

    async def check(self, obj) -> bool:
        data = ctx_data.get()
        user = await customer.get(data["user"])
        return user.is_superuser
