from aiogram.utils.callback_data import CallbackData

from src.utils.keyboards import Constructor

actions_cb = CallbackData("user", "action")
vk_wall_cb = CallbackData("state", "time")
vk_wall_manage_cb = CallbackData("wall", "id", "action")


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
        [3, 1, 2],
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
        {"text": "Задать стены", "cb": ({"action": "vk_add"}, actions_cb)},
        {"text": "Список стен", "cb": ({"action": "vk_view"}, actions_cb)},
        {"text": "Статус", "cb": ({"action": "vk_status"}, actions_cb)},
        {"text": "Назад", "cb": ({"action": "main"}, actions_cb)},
    ],
    [2, 1, 1],
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
