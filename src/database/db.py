from contextlib import asynccontextmanager

from loguru import logger
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


@asynccontextmanager
async def db_session(engine: AsyncEngine) -> AsyncSession:
    session = None
    try:
        async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        session = async_session()
        yield session
        await session.commit()
    except Exception as err:
        logger.exception(err)
        await session.rollback()
    finally:
        await session.close()
