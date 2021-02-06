from loguru import logger
from aiogram import Dispatcher


def filters_setup(dispatcher: Dispatcher):
    logger.info("Configure filters")
    from .superuser import IsSuperUserFilter

    dispatcher.filters_factory.bind(IsSuperUserFilter)
