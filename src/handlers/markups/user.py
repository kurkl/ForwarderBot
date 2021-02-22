from aiogram.utils.callback_data import CallbackData

from src.utils.keyboards import Constructor

user_cb = CallbackData("state", "action")
vk_wall_cb = CallbackData("state", "time")

main_user_menu = Constructor.create_inline_kb(
    [
        {"text": "Вконтакте", "cb": ({"action": "main_vk"}, user_cb)},
        {"text": "Twitter", "cb": ({"action": "main_twitter"}, user_cb)},
    ],
    [2],
)
main_user_vk_menu = Constructor.create_inline_kb(
    [
        {"text": "Задать стены", "cb": ({"action": "add_vk"}, user_cb)},
        {"text": "Список стен", "cb": ({"action": "view_vk"}, user_cb)},
        {"text": "Начать репосты", "cb": ({"action": "start_vk"}, user_cb)},
        {"text": "Пауза", "cb": ({"action": "stop_vk"}, user_cb)},
        {"text": "Статус", "cb": ({"action": "status_vk"}, user_cb)},
        {"text": "Назад", "cb": ({"action": "main"}, user_cb)},
    ],
    [2, 1, 2, 1],
)
user_add_vk_walls = Constructor.create_inline_kb(
    [
        {"text": "30 мин", "cb": ({"time": "add_vk_30"}, vk_wall_cb)},
        {"text": "1 час", "cb": ({"time": "add_vk_60"}, vk_wall_cb)},
        {"text": "2 часа", "cb": ({"time": "add_vk_120"}, vk_wall_cb)},
        {"text": "Custom", "cb": ({"time": "add_vk_c"}, vk_wall_cb)},
        {"text": "Назад", "cb": ({"action": "main_vk"}, user_cb)},
    ],
    [3, 1, 1],
)
main_user_twitter_menu = Constructor.create_inline_kb(
    [
        {"text": "Назад", "cb": ({"action": "main"}, user_cb)},
    ],
    [1],
)
