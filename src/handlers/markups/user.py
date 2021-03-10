from aiogram.utils.callback_data import CallbackData

from src.utils.keyboards import Constructor

actions_cb = CallbackData("user", "action")
vk_wall_cb = CallbackData("state", "time")
vk_wall_manage_cb = CallbackData("wall", "id", "action")
vk_fetch_count_cb = CallbackData("state", "count")


def get_wall_manage_kb(wall_id: int, wall_active: bool):
    change_status = {"text": "Остановить", "cb": ({"id": wall_id, "action": "wall_stop"}, vk_wall_manage_cb)}
    if not wall_active:
        change_status = {"text": "Старт", "cb": ({"id": wall_id, "action": "wall_start"}, vk_wall_manage_cb)}
    return Constructor.create_inline_kb(
        [
            change_status,
            {"text": "Удалить", "cb": ({"id": wall_id, "action": "wall_del"}, vk_wall_manage_cb)},
            {"text": "Назад", "cb": ({"action": "vk_view"}, actions_cb)},
            {"text": "В главное меню", "cb": ({"action": "vk_main"}, actions_cb)},
        ],
        [1, 1, 2],
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


def get_wall_fetch_count_kb(sub_level: int):
    """
    FIXME:
    :param sub_level:
    :return:
    """
    return Constructor.create_inline_kb(
        [
            {"text": "Default", "cb": ({"count": 2}, vk_fetch_count_cb)},
            {"text": "5", "cb": ({"count": 5}, vk_fetch_count_cb)},
            # {"text": "10", "cb": ({"count": 10}, vk_fetch_count_cb)},
            # {"text": "15", "cb": ({"count": 15}, vk_fetch_count_cb)},
            {"text": "Назад", "cb": ({"action": "vk_main"}, actions_cb)},
        ],
        [1, 1, 1],
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
    [1, 1],
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
vk_walls_timeouts_kb = Constructor.create_inline_kb(
    [
        {"text": "30 мин", "cb": ({"time": 30}, vk_wall_cb)},
        {"text": "1 час", "cb": ({"time": 60}, vk_wall_cb)},
        {"text": "2 часа", "cb": ({"time": 120}, vk_wall_cb)},
        # {"text": "Custom", "cb": ({"time": "add_vk_c"}, vk_wall_cb)},
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
