from typing import List, Union, Optional

from loguru import logger
from aiogram.dispatcher.filters.state import State, StatesGroup


def check_num(value: str):
    return True if value.isdigit() else False


class UserVkData(StatesGroup):
    add_wall_id = State()
    add_telegram_id = State()

    # TODO check if values exists

    @staticmethod
    def is_wall_id_valid(raw_data: str) -> bool:
        if check_num(raw_data) and len(raw_data) >= 5:
            return True
        return False

    @staticmethod
    def is_tg_id_valid(raw_data: str) -> bool:
        if check_num(raw_data) and len(raw_data) >= 6:
            return True
        return False
