from typing import List, Union, Optional

from loguru import logger
from aiogram.dispatcher.filters.state import State, StatesGroup


def check_num(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


class UserVkData(StatesGroup):
    set_wall_id = State()
    set_telegram_id = State()
    set_sleep = State()
    set_fetch_count = State()

    # TODO check if values exists

    @staticmethod
    def is_wall_id_valid(raw_data: str) -> bool:
        if check_num(raw_data) and len(raw_data) >= 5:
            return True
        return False

    @staticmethod
    def is_telegram_id_valid(raw_data: str) -> bool:
        if check_num(raw_data) and len(raw_data) >= 6:
            return True
        return False
