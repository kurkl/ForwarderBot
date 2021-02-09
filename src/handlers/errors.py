from loguru import logger
from aiogram.types import Update

from src.runner import dp


@dp.errors_handler()
async def errors_handler(update: Update, exception: Exception):
    try:
        raise exception
    except Exception as ex:
        logger.exception(f"Cause exception {ex} in update {update}")
    return True
