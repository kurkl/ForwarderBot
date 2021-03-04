from datetime import datetime
from dataclasses import dataclass

from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.handler import ctx_data

from src.database import crud


@dataclass
class IsActiveSubscriberFilter(BoundFilter):
    """"""

    key = "is_active_subscriber"
    is_active_subscriber: bool

    async def check(self, obj) -> bool:
        data = ctx_data.get()
        subscriber = await crud.subscriber.get(data["user"].id)
        return subscriber.expiration_dt.date() <= datetime.date(datetime.now())
