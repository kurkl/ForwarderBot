from typing import List, Union, Optional

from aiovk import API, TokenSession
from loguru import logger
from aiogram.dispatcher.filters.state import State, StatesGroup

from src.settings import VK_TOKEN


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

    @staticmethod
    async def get_wall_id_from_domain(short_name: str):
        try:
            async with TokenSession(VK_TOKEN) as session:
                api = API(session)
                wall_object = await api.utils.resolveScreenName(screen_name=short_name)
        except Exception as err:
            logger.error(f"User failed input vk_wall domain {err}")
            return None
        if not wall_object:
            # TODO: if vk.com/club<*****> then
            return None
        if wall_object["type"] == "group":
            return -wall_object["object_id"]
        return wall_object["object_id"]

    @staticmethod
    def is_telegram_id_valid(raw_data: str) -> bool:
        if check_num(raw_data) and len(raw_data) >= 6:
            return True
        return False
        # TODO: check access
