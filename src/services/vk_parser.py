import asyncio
from typing import Dict, List, Union

from loguru import logger
from aiovk.api import API
from aiogram.types import MediaGroup, InputMediaPhoto
from aiovk.sessions import TokenSession

from src.settings import VK_TOKEN
from src.database.entities import VkPostData


def convert_data_to_tg(data: dict) -> Union[str, List[MediaGroup]]:

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
    def __init__(self, bot, wall_ids: Union[int, List[int]]) -> None:
        self._bot = bot
        self._wall_ids = wall_ids

    async def fetch_vk_wall(self) -> Dict[str, Union[str, List[str]]]:
        result_post_record = {"text": "null", "media": {}}
        async with TokenSession(access_token=VK_TOKEN) as session:
            api = API(session)
            try:
                data = await api.wall.get(owner_id=self._wall_ids, count=2, v=5.126)
                current_record = data["items"][1]
            except Exception as err:
                logger.error(err)
            else:
                if "text" in current_record:
                    result_post_record.update({"text": current_record["text"]})
                last_record_id = await VkPostData.get_last_record_id()
                if last_record_id != current_record["id"]:
                    await VkPostData.create_new_post({"idx": current_record["id"], "attachments": False})
                else:
                    result_post_record.update({"text": "no updates"})
                    return result_post_record

                if "attachments" in current_record:
                    await VkPostData.update.values(attachments=True).where(
                        VkPostData.idx == current_record["id"]
                    ).gino.status()
                    result_post_record.update({"media": {"photo": [], "video": []}})

                    for attach in current_record["attachments"]:
                        if attach["type"] == "photo":
                            # TODO: select max? photo size
                            result_post_record["media"]["photo"].append(attach["photo"]["sizes"][-1]["url"])

                return result_post_record


class VkParserBroadcaster(VkParser):
    def __init__(
        self,
        bot,
        wall_ids: Union[int, List[int]],
        target_channels: List[int],
        log_channel: int,
        private: int,
        delay: int = 300,
    ):
        super().__init__(bot, wall_ids)
        self._task = asyncio.Task
        self._target_channels = target_channels
        self._delay = delay
        self._log_channel = log_channel
        self._private = private
        self._status = "STOPPED"

    async def _send_message(self, channel: int, payload: Union[str, dict]) -> None:
        if isinstance(payload, str):
            await self._bot.send_message(channel, payload)
        else:
            await self._bot.send_media_group(channel, payload)

    async def _broadcasting(self) -> None:
        while True:
            content = await self.fetch_vk_wall()
            if content["text"] in ["null", "no updates"]:
                await self._send_message(self._log_channel, content["text"])
            else:
                attach = convert_data_to_tg(content)
                for channel in self._target_channels:
                    await self._send_message(channel, attach)
            await asyncio.sleep(self._delay)

    async def start_broadcasting(self) -> None:
        if self._status != "RUNNING":
            self._task = asyncio.create_task(self._broadcasting())
            self._status = "RUNNING"
            await self._send_message(self._private, "Поехали!")
        else:
            await self._send_message(self._private, "Уже запущено")

    async def stop_broadcasting(self) -> None:
        if self._status != "STOPPED":
            self._task.cancel()
            self._status = "STOPPED"
            await self._send_message(self._private, "Останавливаемся")
        else:
            await self._send_message(self._private, "Уже остановлено")

    def get_status(self) -> str:
        return self._status
