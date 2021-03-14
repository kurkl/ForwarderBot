from aiogram.utils.callback_data import CallbackData

from src.utils.keyboards import Constructor

actions_cb = CallbackData("user", "action")
vk_wall_manage_cb = CallbackData("wall", "idx", "action")
vk_wall_params_cb = CallbackData("wall", "idx", "timeout", "fetch_count")


def get_wall_manage_kb(wall_idx: str, wall_active: bool):
    change_status = {
        "text": "Остановить",
        "cb": ({"idx": wall_idx, "action": "wall_stop"}, vk_wall_manage_cb),
    }
    if not wall_active:
        change_status = {
            "text": "Старт",
            "cb": ({"idx": wall_idx, "action": "wall_start"}, vk_wall_manage_cb),
        }
    return Constructor.create_inline_kb(
        [
            change_status,
            {"text": "Удалить", "cb": ({"idx": wall_idx, "action": "wall_del"}, vk_wall_manage_cb)},
            {
                "text": "Таймаут",
                "cb": ({"idx": wall_idx, "action": "wall_ch_timeout"}, vk_wall_manage_cb),
            },
            {
                "text": "Fetch count",
                "cb": ({"idx": wall_idx, "action": "wall_ch_fetch_count"}, vk_wall_manage_cb),
            },
            {"text": "Назад", "cb": ({"action": "vk_view"}, actions_cb)},
            {"text": "В главное меню", "cb": ({"action": "vk_main"}, actions_cb)},
        ],
        [2, 2, 2],
    )


def get_logs_settings_kb(logs_enabled: bool):
    change_status = {"text": "Выключить", "cb": ({"action": "disable_logs"}, actions_cb)}
    if not logs_enabled:
        change_status = {"text": "Включить", "cb": ({"action": "enable_logs"}, actions_cb)}
    return Constructor.create_inline_kb(
        [
            change_status,
            {"text": "Удалить лог-канал", "cb": ({"action": "remove_logs"}, actions_cb)},
            {"text": "Назад", "cb": ({"action": "main"}, actions_cb)},
        ],
        [2, 1],
    )


def get_wall_fetch_count_kb(wall_idx: str, subscriber_lvl: int):
    """
    FIXME:
    :param subscriber_lvl:
    :param wall_idx:
    :return:
    """
    return Constructor.create_inline_kb(
        [
            {
                "text": "Default",
                "cb": ({"idx": wall_idx, "timeout": "_", "fetch_count": 1}, vk_wall_params_cb),
            },
            {"text": "5", "cb": ({"idx": wall_idx, "timeout": "_", "fetch_count": 5}, vk_wall_params_cb)},
            {"text": "Назад", "cb": ({"action": "vk_main"}, actions_cb)},
        ],
        [2, 1],
    )


back_to_main_menu_kb = Constructor.create_inline_kb(
    [{"text": "В главное меню", "cb": ({"action": "main"}, actions_cb)}], [1]
)

back_to_vk_main_menu_kb = Constructor.create_inline_kb(
    [{"text": "Назад", "cb": ({"action": "vk_main"}, actions_cb)}], [1]
)

main_menu_kb = Constructor.create_inline_kb(
    [
        {"text": "Вконтакте", "cb": ({"action": "vk_main"}, actions_cb)},
        {"text": "Twitter", "cb": ({"action": "twitter_main"}, actions_cb)},
        {"text": "Instagram", "cb": ({"action": "instagram_main"}, actions_cb)},
    ],
    [1, 1, 1],
)
vk_main_menu_kb = Constructor.create_inline_kb(
    [
        {"text": "Добавить стену", "cb": ({"action": "vk_add"}, actions_cb)},
        {"text": "Список стен", "cb": ({"action": "vk_view"}, actions_cb)},
        {"text": "Статус", "cb": ({"action": "vk_status"}, actions_cb)},
        {"text": "Назад", "cb": ({"action": "main"}, actions_cb)},
    ],
    [2, 2],
)


def get_wall_timeout_kb(wall_idx: str):
    return Constructor.create_inline_kb(
        [
            {
                "text": "30 мин",
                "cb": ({"idx": wall_idx, "timeout": 30, "fetch_count": "_"}, vk_wall_params_cb),
            },
            {
                "text": "1 час",
                "cb": ({"idx": wall_idx, "timeout": 60, "fetch_count": "_"}, vk_wall_params_cb),
            },
            {
                "text": "2 часа",
                "cb": ({"idx": wall_idx, "timeout": 120, "fetch_count": "_"}, vk_wall_params_cb),
            },
            {"text": "Назад", "cb": ({"action": "vk_main"}, actions_cb)},
        ],
        [3, 1],
    )


twitter_main_menu_kb = Constructor.create_inline_kb(
    [
        {"text": "Назад", "cb": ({"action": "main"}, actions_cb)},
    ],
    [1],
)

main_user_settings_menu = Constructor.create_default_kb([{"text": "Настройки"}, {"text": "FAQ"}], [2])

user_settings_kb = Constructor.create_inline_kb(
    [
        {"text": "Канал с логами", "cb": ({"action": "logs_channel"}, actions_cb)},
        {"text": "Способ ввода", "cb": ({"action": "change_mode"}, actions_cb)},
        {"text": "Назад", "cb": ({"action": "main"}, actions_cb)},
    ],
    [2, 1],
)
