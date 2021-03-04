from aiogram.utils.callback_data import CallbackData

from src.utils.keyboards import Constructor

actions_cb = CallbackData("user", "action")
vk_wall_cb = CallbackData("state", "time")
vk_wall_manage_cb = CallbackData("wall", "id", "action")
vk_fetch_count_cb = CallbackData("state", "count")


def get_wall_manage_kb(_id: int):
    return Constructor.create_inline_kb(
        [
            {"text": "Старт", "cb": ({"id": _id, "action": "wall_start"}, vk_wall_manage_cb)},
            {"text": "Пауза", "cb": ({"id": _id, "action": "wall_pause"}, vk_wall_manage_cb)},
            {"text": "Продолжить", "cb": ({"id": _id, "action": "wall_resume"}, vk_wall_manage_cb)},
            {"text": "Удалить", "cb": ({"id": _id, "action": "wall_remove"}, vk_wall_manage_cb)},
            {"text": "Назад", "cb": ({"action": "vk_view"}, actions_cb)},
            {"text": "В главное меню", "cb": ({"action": "vk_main"}, actions_cb)},
        ],
        [3, 3],
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


back_to_vk_main_menu_kb = Constructor.create_inline_kb(
    [{"text": "Назад", "cb": ({"action": "vk_main"}, actions_cb)}], [1]
)

main_menu_kb = Constructor.create_inline_kb(
    [
        {"text": "Вконтакте", "cb": ({"action": "vk_main"}, actions_cb)},
        {"text": "Twitter", "cb": ({"action": "twitter_main"}, actions_cb)},
    ],
    [2],
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
