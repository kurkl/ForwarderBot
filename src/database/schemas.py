from typing import Dict, List, Optional
from datetime import datetime, timedelta

from pydantic import BaseModel


class UserBase(BaseModel):
    is_active: Optional[bool] = False
    is_superuser: Optional[bool] = False


class UserCreate(UserBase):
    telegram_id: int


class UserUpdate(UserBase):
    is_active: bool
    is_superuser: Optional[bool] = False
    id: int


class UserInBD(UserBase):
    id: Optional[int] = None


class SubscriberBase(UserInBD):
    subscriber_id: int

    class Config:
        orm_mode = True


class SubscriberCreate(SubscriberBase):
    level: int = 0
    expiration_dt: Optional[datetime] = datetime.now() + timedelta(days=30)


class SubscriberUpdate(SubscriberBase):
    level: int
    expiration_dt: datetime


class TargetBase(SubscriberBase):
    pass


class TargetCreate(TargetBase):
    max_count: int = 5


class TargetUpdate(TargetBase):
    pass


class ForwardBase(BaseModel):
    target_id: int


class ForwardCreate(ForwardBase):
    source_id: int
    source_type: str
    source_short_name: str
    sleep: Optional[int] = 30
    to_chat_id: int
    admin_access: Optional[bool] = False
    fetch_count: int


class ForwardUpdate(ForwardBase):
    source_id: int
    source_type: str
    source_short_name: str
    sleep: int
    to_chat_id: int
    admin_access: Optional[bool]
    fetch_count: int
