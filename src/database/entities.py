import datetime
from typing import Any, Dict

from gino import Gino
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


class VkPostData(TimedBaseModel):
    """"""

    __tablename__ = "vkpostdevdata"

    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    idx = db.Column(db.Integer, nullable=False, unique=True)
    attachments = db.Column(db.Boolean, default=False)

    @classmethod
    async def get_last_post(cls) -> Any:
        last_post = await cls.query.order_by(cls.idx.desc()).gino.first()
        if not last_post:
            await cls.create_new_post({"idx": 1, "attachments": False})
            last_post = await cls.get_last_post()
        return last_post

    @classmethod
    async def create_new_post(cls, data: Dict[str, str]) -> None:
        await cls.create(idx=data["idx"], attachments=data["attachments"])
