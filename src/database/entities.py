import datetime
from typing import Any, Dict, Union

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
    async def get_last_record_id(cls) -> int:
        last_post = await cls.query.order_by(cls.id.desc()).gino.first()
        if not last_post:
            return -1
        return last_post.idx

    @classmethod
    async def create_new_post(cls, data: Dict[str, Union[str, bool]]) -> None:
        await cls.create(idx=data["idx"], attachments=data["attachments"])
