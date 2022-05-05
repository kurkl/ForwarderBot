from enum import Enum

from aiogram.dispatcher.filters.callback_data import CallbackData


class Actions(str, Enum):
    idle = "Главное меню"
    back = "Назад"
    start = "Начать"


class MainUserMenu(str, Enum):
    start = Actions.start
    settings = "Настройки"
    faq = "FAQ"
    idle = Actions.idle


class ProvidersUserMenu(str, Enum):
    vkontakte = "ВКонтакте"
    twitter = "Twitter"
    instagram = "Instagram"
    telegram = "Telegram"
    back = Actions.back


class VkActionsMenu(str, Enum):
    add = "Добавить стену"
    view = "Просмотр стен"
    start = Actions.start
    settings = "Настройки"
    faq = "FAQ"
    status = "Статус"
    back = Actions.back


class UserMenuCallback(CallbackData, prefix="menu"):
    main_nav: MainUserMenu | None = None
    providers_nav: ProvidersUserMenu | None = None


class VkServiceMenuCallback(CallbackData, prefix="vk_menu"):
    main_nav: VkActionsMenu | None = None
