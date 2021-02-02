from typing import Dict, List, Union

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup


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
