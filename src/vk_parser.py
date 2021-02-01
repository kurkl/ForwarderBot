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
    if len(msg_with_media > 9):
        pass

    return msg_with_media


async def fetch_vk_wall(wall_id: int) -> Dict[str, Union[str, List[str]]]:
    result_post_record = {"text": "null"}
    async with TokenSession(access_token=VK_TOKEN) as session:
        api = API(session)
        try:
            data = await api.wall.get(owner_id=wall_id, count=2, v=5.126)
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
                result_post_record.update({"photo": [], "video": []})

                for attach in current_record["attachments"]:
                    if attach["type"] == "photo":
                        # TODO: select max? photo size
                        result_post_record["photo"].append(attach["photo"]["sizes"][-1]["url"])

            return result_post_record
