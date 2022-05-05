import logging
from typing import cast

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

from src.utils.callbacks import (
    Actions,
    MainUserMenu,
    VkActionsMenu,
    UserMenuCallback,
    ProvidersUserMenu,
    VkServiceMenuCallback,
)
from src.handlers.markups.base import BaseMarkups

logger = logging.getLogger(__name__)


class UserMarkups(BaseMarkups):
    def back_to_idle(self, once: bool = False) -> InlineKeyboardButton | ReplyKeyboardMarkup:
        idle = Actions.idle
        if not once:
            return InlineKeyboardButton(
                text=idle,
                callback_data=UserMenuCallback(action=Actions.idle).pack(),
            )

        return (
            self._get_new_builder()
            .button(text=idle, callback_data=UserMenuCallback(action=Actions.idle))
            .as_markup()
        )

    @property
    def main_menu(self) -> InlineKeyboardMarkup:
        builder = self._get_new_builder()
        for item in MainUserMenu:
            builder.button(
                text=item,
                callback_data=UserMenuCallback(main_nav=cast(MainUserMenu, item)),
            )

        return builder.adjust(2, 2).as_markup()

    @property
    def provider_services_menu(self) -> InlineKeyboardMarkup:
        builder = self._get_new_builder()
        for item in ProvidersUserMenu:
            builder.button(
                text=item,
                callback_data=UserMenuCallback(providers_nav=cast(ProvidersUserMenu, item)),
            )
        builder.add(cast(KeyboardButton, self.back_to_idle()))

        return builder.adjust(2, 2, 1).as_markup()

    @property
    def vk_main_menu(self) -> InlineKeyboardMarkup:
        builder = self._get_new_builder()
        for item in VkActionsMenu:
            builder.button(text=item, callback_data=VkServiceMenuCallback(main_nav=cast(VkActionsMenu, item)))

        return builder.adjust(2, 2, 2, 1).as_markup()


user_markups = UserMarkups()
