from typing import Dict, List, Union

from loguru import logger
from aiovk.api import API
from aiogram.types import MediaGroup, InputMediaPhoto
from aiovk.sessions import TokenSession

from src.settings import VK_TOKEN
from src.database.entities import VkPostData


def is_data_valid(data: Dict[str, List]) -> bool:
    text, media = data.get("text"), data.get("attachments")
    if not text and media:
        return False
    return True


def make_telegram_data_to_send(
    data: Dict[str, Union[str, Dict[str, List[str]]]]
) -> Union[str, List[MediaGroup]]:
    if not is_data_valid(data):
        raise ValueError(data)

    if "media" not in data:
        return data["text"]

    msg_with_media = []
    media, caption = data["media"], data["text"]

    if "photo" in media:
        for photo in media["photo"]:
            msg_with_media.append(InputMediaPhoto(photo))
        msg_with_media[0] = InputMediaPhoto(media["photo"][0], caption)
    if "video" in media:
        pass
    if "poll" in media:
        pass
    if "voice" in media:
        pass

    return msg_with_media


async def fetch_vk_wall(wall_id: int) -> dict:
    async with TokenSession(access_token=VK_TOKEN) as session:
        api = API(session)
        try:
            data = await api.wall.get(owner_id=wall_id, count=2)
            record = data["items"][1]
        except Exception as err:
            logger.error(err)
        else:
            if "text" not in record:
                return {"text": "Нет текста"}
            last_post_record = await VkPostData.get_last_post()
            if last_post_record.idx != record["id"]:
                await VkPostData.create_new_post({"idx": record["id"], "attachments": False})
            else:
                return {"text": "Новых постов нет"}

            if "attachments" in record:
                await VkPostData.update.values(attachments=True).where(
                    VkPostData.idx == record["id"]
                ).gino.status()
                media_urls = {"photo": [], "video": []}

                for attach in record["attachments"]:
                    if attach["type"] == "photo":
                        media_urls["photo"].append(attach["photo"]["photo_2560"])

                return {"text": record["text"], "media": media_urls}
            else:
                return {"text": record["text"]}
