from gino import Gino
from sqlalchemy import Column, String, Boolean, Integer, DateTime, BigInteger, ForeignKey, SmallInteger, func
from sqlalchemy.sql import expression
from sqlalchemy.dialects.postgresql import JSONB

db = Gino()


class User(db.Model):
    """
    Stores base client data
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, unique=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    is_superuser = Column(Boolean, server_default=expression.false(), nullable=False)
    is_active = Column(Boolean, server_default=expression.false(), nullable=False)
    created_dt = Column(DateTime, server_default=func.now(), nullable=False)
    updated_dt = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return (
            f"<User (telegram_id={self.telegram_id}, is_active={self.is_active}, "
            f"updated_dt={self.updated_dt.strftime('%Y-%m-%d %H:%M:%S')})> "
        )


class Subscriber(db.Model):
    """
    Stores information about service clients
    3 subscription levels available, by default, each client is level zero (guest)
    """

    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True, unique=True)
    level = Column(SmallInteger, default=0, nullable=False)
    created_dt = Column(DateTime, server_default=func.now(), nullable=False)
    expiration_dt = Column(DateTime, server_default=func.now(), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))

    def __repr__(self):
        return f"<Subscriber (level={self.level}, expiration_dt={self.expiration_dt.strftime('%Y-%m-%d %H:%M:%S')})> "


class ForwarderTarget(db.Model):
    """
    Store subscriber forwarder services data
    """

    __tablename__ = "forwarder_targets"

    id = Column(Integer, primary_key=True, unique=True)
    max_count = Column(SmallInteger, default=10, nullable=False)
    subscriber_walls_data = Column(JSONB, server_default="{}", nullable=False)
    subscriber_id = Column(Integer, ForeignKey("subscribers.id", ondelete="CASCADE", onupdate="CASCADE"))

    def __repr__(self):
        return f"<ForwarderTarget (id={self.id}, max_count={self.max_count})>"


class Target(db.Model):
    """
    Stores info about the sources
    """

    __tablename__ = "targets"

    source_id = Column(BigInteger, primary_key=True)
    type = Column(String)
    sleep = Column(SmallInteger, default=30, nullable=False)
    admin_access = Column(Boolean, server_default=expression.false(), nullable=False)
    created_dt = Column(DateTime, server_default=func.now(), nullable=False)
    updated_dt = Column(DateTime, server_default=func.now(), nullable=False)

    forwarder_target_id = Column(
        Integer, ForeignKey("forwarder_targets.id", ondelete="CASCADE", onupdate="CASCADE")
    )

    def __repr__(self):
        return (
            f"<Target (source_id={self.source_id}, type={self.type}, "
            f"sleep={self.admin_access}, updated_dt={self.updated_dt.strftime('%Y-%m-%d %H:%M:%S')})> "
        )
