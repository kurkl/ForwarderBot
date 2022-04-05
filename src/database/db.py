from loguru import logger
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from contextlib import asynccontextmanager


@asynccontextmanager
async def db_session(engine: AsyncEngine) -> AsyncSession:
    session = None
    try:
        async_session = sessionmaker(engine, echo=True)
        session = async_session()
        yield session
        await session.commit()
    except Exception as err:
        logger.exception(err)
        await session.rollback()
    finally:
        await session.close()
