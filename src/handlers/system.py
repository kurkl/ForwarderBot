import logging

from aiogram import Router, types
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = Router()


@router.message(commands=["health"])
async def healthcheck(message: types.Message, session: AsyncSession):
    """
    Bot health check
    """
    result = await session.execute(text("select now()"))
    await message.reply(result.first()[0].strftime("%d/%m/%Y, %H:%M:%S"))
