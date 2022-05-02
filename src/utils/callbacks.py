from enum import Enum

from aiogram.dispatcher.filters.callback_data import CallbackData


class Actions(str, Enum):
    idle = "Главное меню"
    back = "Назад"
    next = "Вперед"


class MainUserMenu(str, Enum):
    start = "Начать"
    settings = "Настройки"
    faq = "FAQ"


class ProvidersUserMenu(str, Enum):
    vkontakte = "ВКонтакте"
    twitter = "Twitter"
    instagram = "Instagram"
    telegram = "Telegram"


class VkActionsMenu(str, Enum):
    add = "Добавить стену"
    view = "Просмотр стен"
    start = "Начать"
    settings = "Настройки"
    faq = "FAQ"
    status = "Статус"


class UserMenuCallback(CallbackData, prefix="menu"):
    main_nav: MainUserMenu | None = None
    providers_nav: ProvidersUserMenu | None = None
    action: Actions | None = None
