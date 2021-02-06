from typing import Dict, List, Tuple, Union

from aiogram.types import (
    LoginUrl,
    CallbackGame,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.utils.callback_data import CallbackData


def create_keyboard_layout(
    buttons: List[Union[InlineKeyboardButton, KeyboardButton]], count: List[int]
) -> Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]:
    if sum(count) != len(buttons):
        raise ValueError("Количество кнопок не совпадает со схемой")
    tmplist = []
    for a in count:
        tmplist.append([])
        for _ in range(a):
            tmplist[-1].append(buttons.pop(0))
    return tmplist


class DefaultConstructor:
    aliases = {"cb": "callback_data"}
    available_properities = ["text", "callback_data"]
    properties_amount = 1

    @staticmethod
    def create_kb(
        actions: List[Union[str, Dict[str, Union[str, bool]]]],
        schema: List[int],
    ) -> ReplyKeyboardMarkup:
        kb = ReplyKeyboardMarkup()
        kb.row_width = max(schema)
        btns = []
        for a in actions:
            if isinstance(a, str):
                a = {"text": a}
            data: Dict[str, Union[str, bool]] = {}
            for k, v in DefaultConstructor.aliases.items():
                if k in a:
                    a[v] = a[k]
                    del a[k]
            for k in a:
                if k in DefaultConstructor.available_properities:
                    if len(data) < DefaultConstructor.properties_amount:
                        data[k] = a[k]
                    else:
                        break
            if "callback_data" in data:
                data["callback_data"] = data["callback_data"][1].new(**data["callback_data"][0])
            if len(data) != DefaultConstructor.properties_amount:
                raise ValueError("Недостаточно данных для создания кнопки")
            btns.append(KeyboardButton(**data))
        kb.keyboard = create_keyboard_layout(btns, schema)
        kb.resize_keyboard = True
        return kb


class InlineConstructor:
    aliases = {"cb": "callback_data"}
    available_properities = [
        "text",
        "callback_data",
        "url",
        "login_url",
        "switch_inline_query",
        "switch_inline_query_current_chat",
        "callback_game",
        "pay",
    ]
    properties_amount = 2

    @staticmethod
    def create_kb(
        actions: List[
            Dict[
                str,
                Union[
                    str,
                    bool,
                    Tuple[Dict[str, str], CallbackData],
                    LoginUrl,
                    CallbackGame,
                ],
            ]
        ],
        schema: List[int],
    ) -> InlineKeyboardMarkup:
        kb = InlineKeyboardMarkup()
        kb.row_width = max(schema)
        btns = []
        # noinspection DuplicatedCode
        for a in actions:
            data: Dict[
                str,
                Union[
                    str,
                    bool,
                    Tuple[Dict[str, str], CallbackData],
                    LoginUrl,
                    CallbackGame,
                ],
            ] = {}
            for k, v in InlineConstructor.aliases.items():
                if k in a:
                    a[v] = a[k]
                    del a[k]
            for k in a:
                if k in InlineConstructor.available_properities:
                    if len(data) < InlineConstructor.properties_amount:
                        data[k] = a[k]
                    else:
                        break
            if "callback_data" in data:
                data["callback_data"] = data["callback_data"][1].new(**data["callback_data"][0])
            if "pay" in data:
                if len(btns) != 0 and data["pay"]:
                    raise ValueError("Платежная кнопка должна идти первой в клавиатуре")
                data["pay"] = a["pay"]
            if len(data) != InlineConstructor.properties_amount:
                raise ValueError("Недостаточно данных для создания кнопки")
            btns.append(InlineKeyboardButton(**data))
        kb.inline_keyboard = create_keyboard_layout(btns, schema)
        return kb
