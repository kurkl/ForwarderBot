from datetime import datetime, timedelta

from pydantic import BaseModel


class UserBase(BaseModel):
    is_active: bool = True
    is_superuser: bool = False
    phone_number: str | None = None


class UserCreateSchema(UserBase):
    telegram_id: int
