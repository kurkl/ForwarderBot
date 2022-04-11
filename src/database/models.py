from enum import Enum
from uuid import uuid4
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import UUID, JSONB

from .base import BaseModel, TimeStampMixin

# from src.config import settings


class SubscriptionType(Enum):
    FREE = "Free"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    LIFETIME = "Lifetime"


class CommonProvidersTypes(Enum):
    TELEGRAM = "Telegram"
    TWITTER = "Twitter"
    FACEBOOK = "Facebook"


class User(TimeStampMixin):
    """
    Stores data about the user
    """

    __tablename__ = "users"

    id = sa.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    telegram_id = sa.Column(sa.Integer, unique=True, nullable=False, index=True)
    phone_number = sa.Column(sa.String(32), unique=True)
    is_superuser = sa.Column(sa.Boolean, default=False, nullable=False)
    is_active = sa.Column(sa.Boolean, default=True, nullable=False)
    is_subscriber = sa.Column(sa.Boolean, default=False, nullable=False)
    subscription_type = sa.Column(sa.Enum(SubscriptionType), default=SubscriptionType.FREE)
    start_trial_date = sa.Column(sa.DateTime)
    end_trial_date = sa.Column(sa.DateTime)

    def __repr__(self):
        return (
            f"<User(telegram_id={self.telegram_id}, is_active={self.is_active}, "
            # f"updated_dt={self.updated_dt.strftime(settings.TIME_FORMAT)})>"
        )

    @property
    def is_user_active_trial(self) -> bool:
        return self.start_trial_date < datetime.utcnow() <= self.end_trial_date

    @property
    def is_premium_user(self) -> bool:
        return self.subscription_type != SubscriptionType.FREE and self.is_active


class AbstractProvider(BaseModel):
    """
    Common fields for all providers and consumers
    """

    __abstract__ = True

    is_admin_access = sa.Column(sa.Boolean, default=False)
    is_custom = sa.Column(sa.Boolean, default=False)

    @declared_attr
    def type_id(self):
        return sa.Column(sa.ForeignKey("provider_types.id"))


class ProviderType(BaseModel):
    __tablename__ = "provider_types"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.Enum(CommonProvidersTypes), default=CommonProvidersTypes.TELEGRAM, nullable=False)

    def __repr__(self):
        return f"<ProviderType(id={self.id}, name={self.name})>"


class Provider(AbstractProvider, TimeStampMixin):
    """
    Stores data where to forward messages from
    """

    __tablename__ = "providers"

    id = sa.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    user_id = sa.Column(sa.ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))


class Consumer(AbstractProvider, TimeStampMixin):
    """
    Stores data about the consumer services, where the user can send content
    By default its Telegram
    """

    __tablename__ = "consumers"

    id = sa.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    user_id = sa.Column(sa.ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))


class ExchangeSettings(BaseModel):
    """
    Stores params for sending messages from provider to consumer
    """

    __tablename__ = "exchange_settings"

    id = sa.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    provider_id = sa.Column(
        sa.ForeignKey(
            "providers.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        )
    )
    consumer_id = sa.Column(
        sa.ForeignKey(
            "consumers.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        )
    )
    fetch_timeout = sa.Column(sa.SmallInteger, default=30, nullable=False)  # minutes
    extra_params = sa.Column(JSONB)

    # relationships
    provider_messages = relationship("ProviderMessage", back_populates="exchange_settings")

    def __repr__(self):
        return f"<ExchangeSettings(id={self.id}, provider_id={self.provider_id}, consumer_id={self.consumer_id})>"


class ProviderMessage(TimeStampMixin):
    """
    Stores forwarded messages
    """

    __tablename__ = "provider_messages"

    id = sa.Column(UUID(as_uuid=True), default=uuid4, primary_key=True)
    user_id = sa.Column(sa.ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))
    exchange_settings_id = sa.Column(
        sa.ForeignKey(
            "exchange_settings.id",
            ondelete="CASCADE",
            onupdate="CASCADE",
        )
    )
    payload = sa.Column(JSONB)

    # relationships
    exchange_settings = relationship("ExchangeSettings", back_populates="provider_messages")

    def __repr__(self):
        return f"<ProviderMessage(id={self.id}, exchange_settings_id={self.exchange_settings_id})>"
