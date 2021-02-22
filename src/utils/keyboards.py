from typing import Dict, List, Tuple, Union

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData


def create_keyboard_layout(buttons: list, count: List[int]) -> List[list]:
    if sum(count) != len(buttons):
        raise ValueError("Количество кнопок не совпадает со схемой")
    kb_layout = []
    for a in count:
        kb_layout.append([])
        for _ in range(a):
            kb_layout[-1].append(buttons.pop(0))
    return kb_layout


class Constructor:
    aliases = {"cb": "callback_data"}
    available_properities = {
        "default": ["text", "callback_data"],
        "inline": [
            "text",
            "callback_data",
            "url",
            "login_url",
            "switch_inline_query",
            "switch_inline_query_current_chat",
            "pay",
        ],
    }

    @classmethod
    def create_default_kb(
        cls,
        actions: List[Union[str, Dict[str, Union[str, bool]]]],
        schema: List[int],
    ) -> ReplyKeyboardMarkup:
        kb = ReplyKeyboardMarkup()
        kb.row_width = max(schema)
        buttons = []
        for a in actions:
            if isinstance(a, str):
                a = {"text": a}
            data: Dict[str, Union[str, bool]] = {}
            for k, v in cls.aliases.items():
                if k in a:
                    a[v] = a[k]
                    del a[k]
            for k in a:
                if k in cls.available_properities["default"]:
                    data[k] = a[k]
                else:
                    break
            if "callback_data" in data:
                data["callback_data"] = data["callback_data"][1].new(**data["callback_data"][0])
            buttons.append(KeyboardButton(**data))
        kb.keyboard = create_keyboard_layout(buttons, schema)
        kb.resize_keyboard = True
        return kb

    @classmethod
    def create_inline_kb(
        cls,
        actions: List[
            Dict[
                str,
                Union[
                    str,
                    bool,
                    Tuple[Dict[str, str], CallbackData],
                ],
            ]
        ],
        schema: List[int],
    ) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        kb.row_width = max(schema)
        buttons = []
        for a in actions:
            data: Dict[
                str,
                Union[
                    str,
                    bool,
                    Tuple[Dict[str, str], CallbackData],
                ],
            ] = {}
            for k, v in cls.aliases.items():
                if k in a:
                    a[v] = a[k]
                    del a[k]
            for k in a:
                if k in cls.available_properities["inline"]:
                    data[k] = a[k]
                else:
                    break
            if "callback_data" in data:
                data["callback_data"] = data["callback_data"][1].new(**data["callback_data"][0])
            if "pay" in data:
                if len(buttons) != 0 and data["pay"]:
                    raise ValueError("Платежная кнопка должна идти первой в клавиатуре")
                data["pay"] = a["pay"]
            buttons.append(InlineKeyboardButton(**data))
        kb.inline_keyboard = create_keyboard_layout(buttons, schema)
        return kb
