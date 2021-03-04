from typing import Tuple, Union, Optional

from aiovk import API, TokenSession
from loguru import logger
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, ChatAdminRequired
from aiogram.dispatcher.filters.state import State, StatesGroup

from runner import dp
from src.settings import VK_TOKEN


class UserVkData(StatesGroup):
    set_wall_id = State()
    set_telegram_id = State()
    set_sleep = State()
    set_fetch_count = State()

    @staticmethod
    async def get_wall_id_from_domain(short_name: str) -> Optional[int]:
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
    async def get_telegram_id(from_message: Union[str, int]) -> Tuple[int, str]:
        """
        Simple check telegram chat entity is valid
        :param from_message:
        :return: telegram chat id or str error message
        """
        chat_id, error = None, None
        try:
            chat_obj = await dp.bot.get_chat(from_message)
            chat_id = chat_obj.id
        except (ChatNotFound, ChatAdminRequired):
            error = "Чат не существует, или бот не является администратором в группе/канале"
        except BotBlocked:
            error = f"Бот заблокирован в {from_message} чате"
        except Exception as err:
            logger.error(f"User error: {err}")
            error = "Ошибка на стороне сервера"

        return chat_id, error
