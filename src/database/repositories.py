from typing import Any, Type, TypeVar

from loguru import logger
from pydantic import BaseModel
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy.orm import DeclarativeMeta
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncEngine

from src.database import models
from src.database.db import db_session

Model = TypeVar("Model", bound=DeclarativeMeta)
ModelItem = TypeVar("ModelItem", bound=DeclarativeMeta)
Schema = TypeVar("Schema", bound=BaseModel)


def get_repository(repo: Type["BaseRepository"], engine: AsyncEngine) -> callable:
    return repo(engine)


class BaseRepository:
    model: Type[Model] = None

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def create_object(self, obj_data: Schema) -> ModelItem:
        """
        Create new DB object with data from obj_data
        :param obj_data: dict with data for new object
        :return: created object
        """
        async with db_session(self.engine) as session:
            db_object = self.model(**obj_data.dict())
            try:
                session.add(db_object)
            except IntegrityError as err:
                logger.exception(err)
                raise
            await session.commit()
            await session.refresh(db_object)

        return db_object

    async def get_object(self, filters: dict[str, Any] | None = None) -> ModelItem | None:
        """
        Get object from DB by filters
        :param filters: dict with query filters
        :return: object or None
        """
        if not filters:
            filters = {}
        async with db_session(self.engine) as session:
            result = await session.execute(select(self.model).filter_by(**filters))
            db_object = result.scalars().first()

        return db_object

    async def get_objects(
        self,
        limit: int,
        filters: dict[str, Any] | None,
        order_by: list | None = None,
    ) -> list[ModelItem]:
        """
        Get objects from DB by filters
        :param filters: dict with query filters
        :param limit: how many objects to get
        :param order_by: fields to sort by
        :return: list of objects
        """
        if not filters:
            filters = {}
        if not order_by:
            order_by = []

        async with db_session(self.engine) as session:
            result = await session.execute(
                select(self.model).filter_by(**filters).limit(limit).order_by(order_by)
            )
            db_objects = result.scalars().first()

        return db_objects

    async def update_object(self, db_object: ModelItem, obj_update_data: Schema) -> ModelItem:
        """
        Update object in DB
        :param db_object:
        :param obj_update_data: dict with data for updated object
        :return: updated object
        """
        for field, value in obj_update_data.dict().items():
            setattr(db_object, field, value)
        async with db_session(self.engine) as session:
            session.add(db_object)
            await session.commit()
            await session.refresh(db_object)

        return db_object

    async def delete_object(self, filters: dict[str, Any]) -> None:
        """
        Delete object from DB by filters
        :param filters: dict with query filters
        :return: None
        """
        async with db_session(self.engine) as session:
            try:
                db_object = self.get_object(filters)
                await session.delete(db_object)
            except NoResultFound:
                logger.error("Object does not exists")


class UserRepository(BaseRepository):
    model = models.User
