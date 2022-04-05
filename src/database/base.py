import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

BaseModel = declarative_base()


class TimeStampMixin(BaseModel):
    __abstract__ = True

    created_at = sa.Column(sa.DateTime, default=sa.func.now())
    updated_at = sa.Column(sa.DateTime, default=sa.func.now(), onupdate=sa.func.now())
