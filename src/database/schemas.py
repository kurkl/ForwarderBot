from typing import Dict, List, Optional
from datetime import datetime, timedelta

from pydantic import BaseModel


class UserBase(BaseModel):
    is_active: bool = True
    is_superuser: Optional[bool] = False


class UserCreate(UserBase):
    telegram_id: int


class UserUpdate(UserBase):
    is_active = bool
    is_superuser = bool
    telegram_id: int


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


class ForwarderTargetBase(SubscriberBase):
    pass


class ForwarderTargetCreate(ForwarderTargetBase):
    pass


class ForwarderTargetUpdate(ForwarderTargetBase):
    pass


class WallSourceCreate(BaseModel):
    source_id: int
    type: str
    sleep: int = 30
    admin_access: bool = False
    forwarder_target_id: int
