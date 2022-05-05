from typing import Tuple, Union, Optional

from aiogram.dispatcher.filters.state import State, StatesGroup


class UserVkSettings(StatesGroup):
    add_wall_id = State()
    add_telegram_id = State()
    add_timeout = State()
    add_fetch_count = State()

    @staticmethod
    async def get_wall_id_from_public_url(url: str) -> Optional[int]:
        try:
            screen_name, check_id = url.split("/")[-1], None
            async with TokenSession(VK_TOKEN) as session:
                api = API(session)
                wall_object = await api.utils.resolveScreenName(screen_name=screen_name)
                if wall_object:
                    return (
                        -wall_object["object_id"]
                        if wall_object["type"] in ["group", "page"]
                        else wall_object["object_id"]
                    )
                else:
                    if screen_name.startswith("id", 0):
                        check_id = int(screen_name[2:])
                    elif screen_name.startswith("public", 0):
                        check_id = -int(screen_name[6:])
                    elif screen_name.startswith("club", 0):
                        check_id = -int(screen_name[4:])
                    if check_id:
                        check_data = await api.wall.get(owner_id=check_id, count=1)["items"]
                        if check_data:
                            return check_id
                    return check_id
        except Exception as err:
            logger.error(f"User failed input vk_wall url - {err}")
            return None

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


class UserSettings(StatesGroup):
    set_log_channel = State()
    change_wall_input_mode = State()

    @staticmethod
    async def get_log_channel(from_message: str) -> Tuple[int, str]:
        error, channel_id = None, None
        try:
            chat_obj = await dp.bot.get_chat(from_message)
            channel_id = chat_obj.id
        except (BotBlocked, ChatNotFound, ChatAdminRequired):
            error = "Канал или группа не найдена или не установлены админ права"
        except Exception as err:
            logger.error(f"{from_message} another error: {err}")
            error = "Ошибка на стороне сервера"
        return channel_id, error
