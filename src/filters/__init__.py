from aiogram import Dispatcher
from loguru import logger


def filters_setup(dispatcher: Dispatcher):
    logger.info("Configure filters")
    from .superuser import IsSuperUserFilter

    dispatcher.filters_factory.bind(IsSuperUserFilter)

