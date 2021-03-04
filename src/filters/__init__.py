from loguru import logger
from aiogram import Dispatcher


def filters_setup(dispatcher: Dispatcher):
    logger.info("Configure filters")
    from .superuser import IsSuperUserFilter
    from .subscriber import IsActiveSubscriberFilter

    dispatcher.filters_factory.bind(IsSuperUserFilter)
    dispatcher.filters_factory.bind(IsActiveSubscriberFilter)
