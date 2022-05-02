import logging

from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

logger = logging.getLogger(__name__)


class BaseMarkups:
    """
    Base class for all markups
    """

    def __init__(self):
        self._reply_builder = ReplyKeyboardBuilder
        self._inline_builder = InlineKeyboardBuilder

    def _get_new_builder(self, keyboard_type: str = "inline") -> ReplyKeyboardBuilder | InlineKeyboardBuilder:
        """
        Create new builder for selected keyboard type
        :param keyboard_type: str
        :return: new builder instance
        """
        match keyboard_type:
            case "inline":
                return self._inline_builder()
            case "reply":
                return self._reply_builder()
            case _:
                raise ValueError("Incorrect keyboard type")
