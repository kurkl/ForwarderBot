import logging

from aiogram import Router, types
from sqlalchemy import text
from aiogram.utils.markdown import hbold, hlink
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = Router()


@router.message(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет {hbold(message.from_user.full_name)}.\nБот находится в активной разработке,\n"
        "возможны критические баги.\n"
    )


@router.message(commands=["help"])
async def cmd_help(message: types.Message):
    await message.answer("Soon")


@router.message(commands=["contacts"])
async def cmd_feedback(message: types.Message):
    await message.answer(
        "Связь со мной: https://t.me/kurkl\n"
        f"Репозиторий: {hlink('Github', 'https://github.com/kurkl/ForwarderBot')}"
    )


@router.message(commands=["health"])
async def healthcheck(message: types.Message, session: AsyncSession):
    """
    Bot health check
    """
    result = await session.execute(text("select now()"))
    await message.reply(result.first()[0].strftime("%d/%m/%Y, %H:%M:%S"))
