import asyncio
from typing import Dict, List, Union

import aiojobs
from loguru import logger
from aiovk.api import API
from aiogram.types import InputMediaPhoto
from aiovk.sessions import TokenSession

from src.database.entities import User, VkPostData


def convert_data_to_tg(data: dict) -> Union[str, List[InputMediaPhoto]]:
    msg_with_media = []
    media, caption = data["media"], data["text"]

    if "photo" in media:
        for photo in media["photo"]:
            msg_with_media.append(InputMediaPhoto(photo))
        msg_with_media[0] = InputMediaPhoto(media["photo"][0], caption)
    if "video" in media:
        pass

    if not msg_with_media:
        return caption
    else:
        return msg_with_media


class VkParser:
    """
    Parse vk source with https://vk.com/dev/methods
    """

    def __init__(self, wall_ids, token, user):
        self._wall_ids = wall_ids
        self._token = token
        self._user = user

    async def fetch_vk_wall(self) -> Dict[str, Union[str, List[str]]]:
        result_post_record = {"text": "null", "media": {"photo": [], "video": []}}
        async with TokenSession(access_token=self._token) as session:
            api = API(session)
            try:
                data = await api.wall.get(owner_id=self._wall_ids, count=2, v=5.126)
                current_record = data["items"][1]
            except Exception as err:
                logger.error(err)
            else:
                if "text" in current_record:
                    result_post_record.update({"text": current_record["text"]})
                last_record_id = await VkPostData.get_last_record_id(self._user.id)
                if last_record_id != current_record["id"]:
                    await VkPostData.create_new_record(
                        {"user_id": self._user.id, "id": current_record["id"], "attachments": False}
                    )
                else:
                    result_post_record.update({"text": "no updates"})
                    return result_post_record

                if "attachments" in current_record:
                    await VkPostData.update.values(attachments=True).where(
                        VkPostData.id == current_record["id"]
                    ).gino.status()

                    for attach in current_record["attachments"]:
                        if attach["type"] == "photo":
                            # TODO: select max? photo size
                            result_post_record["media"]["photo"].append(attach["photo"]["sizes"][-1]["url"])

                return result_post_record


class VkBroadcaster(VkParser):
    """
    TODO: Need custom delay for each channel
    """

    def __init__(self, bot, wall_ids, user, target_channels, log_channel, private, token, delay):
        super().__init__(wall_ids, token, user)
        self._bot = bot
        self._target_channels = target_channels
        self._delay = delay
        self._log_channel = log_channel
        self._private = private

    async def _async_init(self):
        """
        Async class init or get background object
        :return: background task instance
        """
        if hasattr(self, "_broadcaster"):
            if not self._broadcaster.closed:
                return
        self._broadcaster = await aiojobs.create_scheduler()
        return self

    # def __await__(self):
    #     """
    #     Await constructor
    #     """
    #     return self._async_init().__await__()

    async def _send_message(self, channel: int, payload: Union[str, list]):
        """
        Send bot text message or message with media attach
        :param channel: telegram channel id
        :param payload: text or text with media
        """
        if isinstance(payload, str):
            await self._bot.send_message(channel, payload)
        else:
            await self._bot.send_media_group(channel, payload)

    async def _broadcasting(self):
        while True:
            content = await self.fetch_vk_wall()
            if content["text"] in ["null", "no updates"]:
                await self._send_message(self._log_channel, content["text"])
            else:
                attach = convert_data_to_tg(content)
                for channel in self._target_channels:
                    await self._send_message(channel, attach)

            await asyncio.sleep(self._delay)

    async def start_broadcasting(self):
        """
        Run background vk source parsing
        """
        if self._broadcaster.active_count == 0:
            await self._send_message(self._private, "Поехали!")
            await self._broadcaster.spawn(self._broadcasting())
        else:
            await self._send_message(self._private, "Уже запущено")

    async def stop_broadcasting(self):
        if self._broadcaster.active_count > 0:
            await self._send_message(self._private, "Останавливаемся")
            await self._broadcaster.close()
        else:
            await self._send_message(self._private, "Уже остановлено")

    async def get_loop(self):
        await self._async_init()

    @property
    def status(self) -> int:
        return self._broadcaster.active_count


def create_broadcaster(
    bot,
    wall_ids: List[int],
    target_channels: List[int],
    log_channel: int,
    private: int,
    user: User,
    token: str = None,
    delay: int = 300,
):
    return VkBroadcaster(
        bot,
        wall_ids=wall_ids,
        token=token,
        target_channels=target_channels,
        log_channel=log_channel,
        private=private,
        delay=delay,
        user=user,
    )
