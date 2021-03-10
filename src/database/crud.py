from typing import Any, List

from loguru import logger

from .schemas import (
    UserCreate,
    UserUpdate,
    TargetCreate,
    ForwardCreate,
    ForwardUpdate,
    SubscriberCreate,
    SubscriberUpdate,
)
from .entities import User, Target, Forward, Subscriber


class CRUDBase:
    """
    Templates basic database operations for all models
    """

    def __init__(self, model):
        self.model = model

    async def get(self, _id: Any):
        return await self.model.query.where(self.model.id == _id).gino.first()

    async def get_multi(self, offset: int = 0, limit: int = 100):
        return await self.model.query.offset(offset).limit(limit).gino.all()

    async def create(self, values: dict):
        await self.model.create(**values)

    async def update(self, values: dict):
        await self.model.update(**values).apply()

    async def remove(self, _id: int):
        await self.model.delete.where(self.model.id == _id).gino.status()


class CRUDUser(CRUDBase):
    async def get(self, telegram_id: int) -> User:
        return await User.query.where(User.telegram_id == telegram_id).gino.first()

    async def create(self, values: UserCreate) -> User:
        obj = {
            "telegram_id": values.telegram_id,
            "is_active": values.is_active,
            "is_superuser": values.is_superuser,
        }
        return await User.create(**obj)

    async def update(self, values: UserUpdate):
        obj = {
            "is_active": values.is_active,
            "is_superuser": values.is_superuser,
            "id": values.id,
        }
        await User.update(**obj).apply()

    async def remove(self, _id: User.telegram_id):
        await User.delete.where(User.telegram_id == _id).gino.status()


class CRUDSubscriber(CRUDBase):
    async def get(self, user_id: int) -> Subscriber:
        return await Subscriber.query.where(Subscriber.user_id == user_id).gino.first()

    async def create(self, values: SubscriberCreate) -> Subscriber:
        obj = {
            "level": values.level,
            "expiration_dt": values.expiration_dt,
            "user_id": values.subscriber_id,
        }
        return await Subscriber.create(**obj)

    async def update(self, values: SubscriberUpdate):
        obj = {
            "level": values.level,
            "expiration_dt": values.expiration_dt,
            "user_id": values.subscriber_id,
        }
        await Subscriber.update(**obj).apply()

    async def get_multi_by_level(self, level: int, limit: int = 100) -> List[Subscriber]:
        """
        Outputs subscribers with specific sub level
        :param level: 0-3
        :param limit: how much output
        :return:
        """
        return await Subscriber.query.where(Subscriber.level == level).limit(limit).gino.all()


class CRUDTargets(CRUDBase):
    async def get(self, subscriber_id: int) -> Target:
        return await Target.query.where(Target.subscriber_id == subscriber_id).gino.first()

    async def create(self, values: TargetCreate):
        obj = {"subscriber_id": values.subscriber_id, "max_count": values.max_count}
        await Target.create(**obj)

    async def remove(self, subscriber_id: int):
        await Target.delete.where(Target.id == subscriber_id).gino.status()

    async def add_source(self, values: ForwardCreate):
        obj = {
            "source_id": values.source_id,
            "source_type": values.source_type,
            "source_short_name": values.source_short_name,
            "sleep": values.sleep,
            "to_chat_id": values.to_chat_id,
            "target_id": values.target_id,
            "fetch_count": values.fetch_count,
        }
        await Forward.create(**obj)

    async def get_sources_data(self, target_id: int) -> List[Forward]:
        return await Forward.query.where(
            (Forward.target_id == target_id) & ~(Forward.source_type == "logs")
        ).gino.all()

    async def get_source_data(self, source_id: Forward.source_id, target_id: int) -> Forward:
        return await Forward.query.where(
            (Forward.source_id == source_id) & (Forward.target_id == target_id)
        ).gino.first()

    async def update_sources_data(self, values: ForwardUpdate):
        obj = {
            "source_id": values.source_id,
            "source_type": values.source_type,
            "source_short_name": values.source_short_name,
            "sleep": values.sleep,
            "to_chat_id": values.to_chat_id,
            "target_id": values.target_id,
            "fetch_count": values.fetch_count,
        }
        return await Forward.update(**obj).apply()

    async def remove_source_data(self, source_id: int, target_id: int):
        source = await Forward.query.where(
            (Forward.target_id == target_id) & (Forward.source_id == source_id)
        ).gino.first()
        if source:
            await source.delete()
        else:
            logger.warning(f"Value {source_id} does not exist")

    async def get_log_channel(self, target_id: int) -> Forward:
        return await Forward.query.where(
            (Forward.target_id == target_id) & (Forward.source_type == "logs")
        ).gino.first()


target = CRUDTargets(Target)
user = CRUDUser(User)
subscriber = CRUDSubscriber(Subscriber)
