import asyncio
from typing import Dict, List, Union

from loguru import logger
from aiovk.api import API
from aiogram.types import MediaGroup, InputMediaPhoto
from aiovk.sessions import TokenSession

from src.settings import VK_TOKEN
from src.database.entities import VkPostData


class VkParser:
    def __init__(self, bot, wall_ids: Union[int, List[int]]) -> None:
        self.bot = bot
        self.wall_ids = wall_ids

    async def fetch_vk_wall(self) -> Dict[str, Union[str, List[str]]]:
        result_post_record = {"text": "null"}
        async with TokenSession(access_token=VK_TOKEN) as session:
            api = API(session)
            try:
                data = await api.wall.get(owner_id=self.wall_ids, count=2, v=5.126)
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

    def convert_data_to_tg(
        self, data: Dict[str, Union[str, Dict[str, List[str]]]]
    ) -> Union[str, List[MediaGroup]]:

        msg_with_media = []
        media, caption = data["media"], data["text"]

        if "photo" in media:
            for photo in media["photo"]:
                msg_with_media.append(InputMediaPhoto(photo))
            msg_with_media[0] = InputMediaPhoto(media["photo"][0], caption)
        if "video" in media:
            pass

        return msg_with_media


class VkParserBroadcaster(VkParser):
    status = "STOPPED"

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
        self.task = asyncio.Task
        self.target_channels = target_channels
        self.delay = delay
        self.log_channel = log_channel
        self.private = private

    async def _send_message(self, channel: int, payload) -> None:
        if isinstance(payload, str):
            await self.bot.send_message(channel, payload)
        else:
            await self.bot.send_media_group(channel, payload)

    async def broadcasting(self) -> None:
        while True:
            content = await self.fetch_vk_wall()
            if content["text"] in ["null", "no updates"]:
                await self._send_message(self.log_channel, content["text"])
            else:
                attach = self.convert_data_to_tg(content)
                for channel in self.target_channels:
                    await self._send_message(channel, attach)
            await asyncio.sleep(self.delay)

    async def start_broadcasting(self) -> None:
        if self.status != "RUNNING":
            self.task = asyncio.create_task(self.broadcasting())
            self.status = "RUNNING"
            await self._send_message(self.private, "Поехали!")
        else:
            await self._send_message(self.private, "Уже запущено")

    async def stop_broadcasting(self) -> None:
        if self.status != "STOPPED":
            self.task.cancel()
            self.status = "STOPPED"
            await self._send_message(self.private, "Останавливаемся")
        else:
            await self._send_message(self.private, "Уже остановлено")

    def get_status(self) -> str:
        return self.status
