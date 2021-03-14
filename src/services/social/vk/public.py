from typing import Dict, List, Union, Optional
from contextlib import asynccontextmanager

import tenacity
from aiovk import API, TokenSession
from loguru import logger


class VkFetch:
    def __init__(self, token: str):
        self.token = token

    @asynccontextmanager
    async def _session(self):
        session = TokenSession(access_token=self.token)
        try:
            yield API(session)
        except Exception as err:
            logger.error(f"Error: {err}")
            raise
        finally:
            await session.close()

    @tenacity.retry(wait=tenacity.wait_fixed(2), stop=tenacity.stop_after_attempt(2))
    async def fetch_public_wall(self, wall_id: int, fetch_count: int) -> List[Dict[str, Union[str, List]]]:
        """
        Get public vk data with wall.get method
        :param fetch_count:
        :param wall_id: vkontakte wall_id
        :return:
        """
        fetch_result = []
        async with self._session() as session:
            received_records = await session.wall.get(owner_id=wall_id, count=fetch_count + 1, v=5.145)
            if "is_pinned" in received_records["items"][0]:
                records = received_records["items"][1:]
            else:
                records = received_records["items"][:-1]

            for record in records:
                if "is_pinned" in record:
                    continue
                item = {"date": record["date"], "post_id": record["id"]}
                if "text" in record:
                    item.update({"text": record["text"]})
                if "attachments" in record:
                    item.update({"media": {"photos": [], "videos": [], "poll": {}}})
                    for attach in record["attachments"]:
                        if attach["type"] == "photo":
                            item["media"]["photos"].append(attach["photo"]["sizes"][-1]["url"])
                        if attach["type"] == "video":
                            # video_item = await session.video.get(
                            #     owner_id=wall_id, videos=f"{wall_id}_{attach['video']['id']}"
                            # )
                            # file_url_key = list(video_item["items"][0]["files"])[-2]
                            # item["media"]["videos"].append(video_item["items"][0]["files"][file_url_key])
                            item["media"]["videos"].append("Not supported!")
                        if attach["type"] == "poll":
                            item["media"]["poll"].update(
                                {
                                    "question": attach["poll"]["question"],
                                    "anonymous": attach["poll"]["anonymous"],
                                    "answers": attach["poll"]["answers"],
                                }
                            )
                if "media" in item:
                    for media_type in item["media"].copy():
                        if not item["media"][media_type]:
                            item["media"].pop(media_type)
                fetch_result.append(item)

        return fetch_result
