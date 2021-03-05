import json
from typing import List, Union, Optional
from datetime import datetime
from contextlib import asynccontextmanager

import tenacity
from aiovk import API, TokenSession
from loguru import logger
from aiogram import Dispatcher
from aiogram.types import InputMediaPhoto
from apscheduler.job import Job
from apscheduler.events import JobExecutionEvent
from aiogram.utils.executor import Executor
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, ChatAdminRequired
from apscheduler.triggers.interval import IntervalTrigger

from src.runner import bot
from src.settings import VK_TOKEN, REDIS_URI, REDIS_DB_CACHE
from src.utils.redis import RedisPool
from src.utils.scheduler import scheduler


class TelegramSender:
    @classmethod
    def prepare_message(cls, msg_data: dict) -> Union[str, List[InputMediaPhoto]]:
        result = []
        media, caption = msg_data.get("media"), msg_data.get("text")

        if not media:
            return caption

        if not media["photos"] and not media["videos"] and not media["audio"] and not media["polls"]:
            return caption

        if "photos" in media:
            for photo in media["photos"]:
                result.append(InputMediaPhoto(photo))
            if caption:
                result[0] = InputMediaPhoto(media["photos"][0], caption)

        return result

    @classmethod
    async def send(cls, chat_id: int, raw_message: dict):
        try:
            message = cls.prepare_message(raw_message)
            if isinstance(message, str):
                await bot.send_message(chat_id=chat_id, text=message)
            else:
                await bot.send_media_group(chat_id=chat_id, media=message)
        except ChatNotFound:
            logger.error(f"Chat {chat_id} not found")
        except ChatAdminRequired:
            logger.error(f"Chat {chat_id} admin required")
        except (BotBlocked, Exception) as err:
            logger.error(f"Another bot error: {err}")


class VkFetch(RedisPool):
    def __init__(self, token: str):
        super(VkFetch, self).__init__(REDIS_URI, REDIS_DB_CACHE)
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

    async def execute_event(self, cache_name: str, user_store: str):
        redis_data = await self.redis.hget(cache_name, user_store, encoding="utf-8")
        event_data = json.loads(redis_data)
        if event_data["delivery"] == "auto":
            for msg in event_data["items"]:
                await TelegramSender.send(event_data["to_chat_id"], msg),
        elif event_data["delivery"] == "timeout":
            pass

    @tenacity.retry(wait=tenacity.wait_fixed(2), stop=tenacity.stop_after_attempt(2))
    async def fetch_public_wall(self, user_id: int, wall_id: int, to_chat_id: int, count):
        """
        FIXME:
        Get public vk data with wall.get method
        :param count:
        :param user_id: telegram user_id
        :param wall_id: vkontakte wall_id
        :param to_chat_id: telegram id channel, group or user id
        :return:
        """

        cache_name, user_store = f"{user_id}:cache", f"{wall_id}:{to_chat_id}"
        redis_cache_data = await self.redis.hget(cache_name, user_store, encoding="utf-8")
        cache_data = json.loads(redis_cache_data)
        fetch_result = {
            "to_chat_id": cache_data["to_chat_id"],
            "delivery": cache_data["delivery"],
            "items": [],
        }
        # await asyncio.sleep(uniform(0.150, 0.350))

        async with self._session() as session:
            received_records = await session.wall.get(owner_id=wall_id, count=count, v=5.126)

        for record in received_records["items"][1:]:
            item = {"date": record["date"]}
            if "text" in record:
                item.update({"text": record["text"]})
            if "attachments" in record:
                item.update({"media": {"photos": [], "videos": [], "audio": [], "polls": []}})
                for attach in record["attachments"]:
                    if attach["type"] == "photo":
                        item["media"]["photos"].append(attach["photo"]["sizes"][-1]["url"])
                    # TODO: get video, polls, voice etc
            if item not in cache_data["items"]:
                fetch_result["items"].append(item)

        if fetch_result["items"]:
            await self.redis.hset(
                cache_name, user_store, json.dumps(fetch_result, ensure_ascii=False).encode("utf-8")
            )
            await self.execute_event(cache_name, user_store)
        else:
            logger.warning(f"wall_id: {wall_id} no new post")


class VkScheduler(VkFetch):
    def event_listener(self, event: JobExecutionEvent):
        pass

    def get_user_jobs(self, user_id: int) -> Optional[List[Job]]:
        job_list = scheduler.get_jobs()
        if job_list:
            return [job for job in job_list if user_id == job.args[0]]
        else:
            return None

    def _get_job_by_id(self, *args: int) -> Optional[Job]:
        return scheduler.get_job(f"{args[0]}:{args[1]}:{args[2]}")

    async def _get_data_from_redis(self, *args: int) -> Optional[dict]:
        """
        :param args: (user_id, from_wall, to_channel)
        :return:
        """
        redis_data = await self.redis.hget(f"{args[0]}:cache", f"{args[1]}:{args[2]}", encoding="utf-8")
        return json.loads(redis_data) if redis_data else None

    def add_job(self, user_id: int, wall_id: int, to_chat_id: int, timeout: int, fetch_count: int):
        job = self._get_job_by_id(user_id, wall_id, to_chat_id)
        if not job:
            scheduler.add_job(
                self.fetch_public_wall,
                IntervalTrigger(seconds=timeout),
                args=(
                    user_id,
                    wall_id,
                    to_chat_id,
                    fetch_count,
                ),
                id=f"{user_id}:{wall_id}:{to_chat_id}",
                next_run_time=datetime.now(),
            )
        else:
            logger.warning("The task is already in progress")

    async def update_delivery_settings(self, user_id: int, wall_id: int, to_chat_id: int, param: str):
        latest_data = await self._get_data_from_redis(user_id, wall_id, to_chat_id)
        if not latest_data:
            new_data = {"to_chat_id": to_chat_id, "delivery": param, "items": []}
            await self.redis.hset(
                f"{user_id}:cache",
                f"{wall_id}:{to_chat_id}",
                json.dumps(new_data, ensure_ascii=False).encode("utf-8"),
            )
        else:
            latest_data.update({"delivery": param})
            await self.redis.hset(
                f"{user_id}:cache",
                f"{wall_id}:{to_chat_id}",
                json.dumps(latest_data, ensure_ascii=False).encode("utf-8"),
            )

    async def remove_job(self, user_id: int, wall_id: int, to_chat_id: int):
        job = self._get_job_by_id(user_id, wall_id, to_chat_id)
        if job:
            scheduler.remove_job(job.id)
            await self.redis.hdel(f"{user_id}:cache", f"{wall_id}:{to_chat_id}")
        else:
            logger.warning("No such task")

    def pause_job(self, user_id: int, wall_id: int, to_chat_id: int):
        job = self._get_job_by_id(user_id, wall_id, to_chat_id)
        if job:
            scheduler.pause_job(job.id)
        else:
            logger.warning("No such task")

    def continue_job(self, user_id: int, wall_id: int, to_chat_id: int):
        job = self._get_job_by_id(user_id, wall_id, to_chat_id)
        if job:
            scheduler.resume_job(job.id)
        else:
            logger.warning("No such task")


vk_scheduler = VkScheduler(VK_TOKEN)


# scheduler.add_listener(vk_scheduler.event_listener, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)


async def on_startup(dispatcher: Dispatcher):
    await vk_scheduler.connect()
    logger.info("Start vk broadcaster")


async def on_shutdown(dispatcher: Dispatcher):
    await vk_scheduler.connect()
    logger.info("Shutdown vk broadcaster")


def vk_scheduler_setup(runner: Executor):
    runner.on_startup(on_startup)
    runner.on_shutdown(on_shutdown)
