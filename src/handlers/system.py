import logging

from aiogram import Router, types
from sqlalchemy import text
from aiogram.utils.markdown import hbold, hlink
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.constants import DEFAULT_HELLO_MESSAGE
from src.handlers.markups import user_markups

logger = logging.getLogger(__name__)

router = Router()


@router.message(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer(
        text=DEFAULT_HELLO_MESSAGE.format(hbold(message.from_user.full_name)),
        reply_markup=user_markups.main_menu,
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
async def cmd_healthcheck(message: types.Message, session: AsyncSession):
    """
    Bot health check
    """
    result = await session.execute(text("select now()"))
    await message.reply(result.first()[0].strftime("%d/%m/%Y, %H:%M:%S"))


@router.errors()
async def catch_errors(update: types.Update, exception: Exception):
    try:
        raise exception
    except Exception as err:
        logger.exception(f"Cause exception {err} an update {update}")
    return True
