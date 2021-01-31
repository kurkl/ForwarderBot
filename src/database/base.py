# Import all the models, so that Base has them before being
# imported by Alembic

from .entities import VkPostData, db

__all__ = ("db", "VkPostData")
