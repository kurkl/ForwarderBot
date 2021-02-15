import datetime
from typing import Dict

from gino import Gino
from loguru import logger
from sqlalchemy import inspect

db = Gino()


class BaseModel(db.Model):
    __abstract__ = True

    def __str__(self):
        model = self.__class__.__name__
        table = inspect(self.__class__)
        primary_key_columns = table.primary_key.columns
        values = {
            column.name: getattr(self, self._column_name_map[column.name]) for column in primary_key_columns
        }
        values_str = " ".join(f"{name}={value!r}" for name, value in values.items())
        return f"<{model} {values_str}>"


class TimedBaseModel(BaseModel):
    __abstract__ = True

    created_at = db.Column(db.DateTime(True), server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime(True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        server_default=db.func.now(),
    )


class User(TimedBaseModel):
    """"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    is_superuser = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=False)

    @classmethod
    async def get(cls, user_id: int):
        query = await cls.query.where(cls.id == user_id).gino.first()
        return query

    @classmethod
    async def create_superuser(cls, superuser_id: int):
        user = await cls.get(superuser_id)
        if not user:
            await cls.create(id=superuser_id, is_superuser=True, is_active=True)
        elif not user.is_superuser or not user.is_active:
            await cls.update.where(cls.id == superuser_id).values(is_superuser=True, is_active=True).apply()
        else:
            logger.warning(f"User id {superuser_id} is already an superuser")


class Chat(TimedBaseModel):
    """"""

    __tablename__ = "chats"

    id = db.Column(db.Integer, primary_key=True, unique=True)
    type = db.Column(db.String(20))

    @classmethod
    async def get(cls, chat_id: int):
        query = await cls.query.where(cls.id == chat_id).gino.first()
        return query


class VkPostData(TimedBaseModel):
    """
    Stores the history of the parser operations
    """

    __tablename__ = "vkpostdata"

    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey(f"{User.__tablename__}.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    has_attachments = db.Column(db.Boolean, default=False)

    @classmethod
    async def get_last_record_id(cls, user_id: int) -> int:
        last_post = await cls.query.where(cls.user_id == user_id).order_by(cls.id.desc()).gino.first()
        if not last_post:
            return -1
        return last_post.vk_record_id

    @classmethod
    async def create_new_record(cls, data: Dict[str, bool]):
        await cls.create(user_id=data["user_id"], id=data["id"], has_attachments=data["attachments"])
