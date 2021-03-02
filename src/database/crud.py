from typing import Any, List

from loguru import logger

from .schemas import (
    UserCreate,
    UserUpdate,
    SubscriberCreate,
    SubscriberUpdate,
    WallSourceCreate,
    WallSourceUpdate,
    ForwarderTargetCreate,
)
from .entities import User, Target, Subscriber, ForwarderTarget


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
    async def get(self, _id: User.telegram_id) -> User:
        return await User.query.where(User.telegram_id == _id).gino.first()

    async def create(self, values: UserCreate) -> User:
        obj = {
            "telegram_id": values.telegram_id,
            "is_active": values.is_active,
            "is_superuser": values.is_superuser,
        }
        return await User.create(**obj)

    async def update(self, values: UserUpdate):
        obj = {
            "telegram_id": values.telegram_id,
            "is_active": values.is_active,
            "is_superuser": values.is_superuser,
        }
        await User.update(**obj).apply()

    async def remove(self, _id: User.telegram_id):
        await User.delete.where(User.telegram_id == _id).gino.status()


class CRUDSubscriber(CRUDBase):
    async def get(self, _id: User.id) -> Subscriber:
        return await Subscriber.query.where(Subscriber.user_id == _id).gino.first()

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


class CRUDForwarderTargets(CRUDBase):
    async def get(self, _id: Subscriber.id) -> ForwarderTarget:
        return await ForwarderTarget.query.where(ForwarderTarget.subscriber_id == _id).gino.first()

    async def create(self, values: ForwarderTargetCreate):
        obj = {"subscriber_id": values.subscriber_id}
        await ForwarderTarget.create(**obj)

    async def remove(self, _id: Subscriber.id):
        await ForwarderTarget.delete.where(ForwarderTarget.id == _id).gino.status()

    async def add_source(self, values: WallSourceCreate):
        obj = {
            "source_id": values.source_id,
            "type": values.type,
            "sleep": values.sleep,
            "telegram_target_id": values.telegram_target_id,
            "forwarder_target_id": values.forwarder_target_id,
            "fetch_count": values.fetch_count,
        }
        await Target.create(**obj)

    async def get_sources_data(self, _id: ForwarderTarget.id) -> List[Target]:
        return await Target.query.where(Target.forwarder_target_id == _id).gino.all()

    async def get_source_data(self, source_id: Target.source_id, _id: ForwarderTarget.id) -> Target:
        return await Target.query.where(
            Target.source_id == source_id and Target.forwarder_target_id == _id
        ).gino.first()

    async def update_sources_data(self, values: WallSourceUpdate):
        obj = {
            "source_id": values.source_id,
            "type": values.type,
            "sleep": values.sleep,
            "forwarder_target_id": values.forwarder_target_id,
            "fetch_count": values.fetch_count,
        }
        return await Target.update(**obj).apply()

    async def remove_source_data(self, source_id: int, _id: ForwarderTarget.id):
        source = await Target.query.where(
            Target.forwarder_target_id == _id and Target.source_id == source_id
        ).gino.first()
        if source:
            await source.delete()
        else:
            logger.warning(f"Value {source_id} does not exist")


forwarder = CRUDForwarderTargets(ForwarderTarget)
user = CRUDUser(User)
subscriber = CRUDSubscriber(Subscriber)
