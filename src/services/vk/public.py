import json
import asyncio
from random import uniform
from typing import List, Union, Optional
from datetime import datetime
from contextlib import asynccontextmanager

import tenacity
from aiovk import API, TokenSession
from loguru import logger
from aiogram import Dispatcher
from aiogram.types import MediaGroup, InputMediaPhoto, InlineKeyboardMarkup
from apscheduler.job import Job
from apscheduler.events import JobExecutionEvent
from aiogram.utils.executor import Executor
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, ChatAdminRequired
from aiogram.utils.callback_data import CallbackData
from apscheduler.triggers.interval import IntervalTrigger

from src.runner import bot
from src.settings import VK_TOKEN, REDIS_URI, REDIS_DB_CACHE
from src.utils.redis import RedisPool
from src.utils.keyboards import Constructor
from src.utils.scheduler import scheduler

vk_scheduler_cb = CallbackData("state", "id", "action")

confirm_kb = Constructor.create_inline_kb(
    [{"text": "Ок", "cb": ({"id": -1, "action": "confirm"}, vk_scheduler_cb)}], [1]
)


def make_respond_kb(target_id) -> InlineKeyboardMarkup:
    return Constructor.create_inline_kb(
        [
            {"text": "Опубликовать сейчас", "cb": ({"id": target_id, "action": "now"}, vk_scheduler_cb)},
            {"text": "Таймаут", "cb": ({"id": target_id, "action": "timeout"}, vk_scheduler_cb)},
            {"text": "Авто репосты", "cb": ({"id": target_id, "action": "auto"}, vk_scheduler_cb)},
        ],
        [1, 1, 1],
    )


class TelegramSender:
    @classmethod
    def prepare_message(cls, msg_data: dict) -> List[InputMediaPhoto]:
        result = []
        media, caption = msg_data["media"], msg_data["text"]

        if "photos" in media:
            for photo in media["photos"]:
                result.append(InputMediaPhoto(photo))
            if caption:
                result[0] = InputMediaPhoto(media["photos"][0], caption)

        return result

    @classmethod
    async def send(cls, chat_id: int, message: Union[str, dict]):
        try:
            if isinstance(message, str):
                await bot.send_message(chat_id=chat_id, message=message)
            else:
                message_with_media = cls.prepare_message(message)
                await bot.send_media_group(chat_id=chat_id, media=message_with_media)
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

    @tenacity.retry(wait=tenacity.wait_fixed(2), stop=tenacity.stop_after_attempt(2))
    async def fetch_public_wall(self, user_id: int, wall_id: int, target_id: int, count):
        """
        FIXME:
        Get public vk data with wall.get method
        :param count:
        :param user_id: telegram user_id
        :param wall_id: vkontakte wall_id
        :param target_id: telegram id channel, group or user id
        :return:
        """

        cache_name, user_store = f"{user_id}:cache", f"{wall_id}:{target_id}"
        redis_data = await self.redis.hget(cache_name, user_store, encoding="utf-8")
        fetch_result = {"target_id": target_id, "items": []}
        cache_data = json.loads(redis_data) if redis_data else {"delivery": "", "items": []}
        fetch_result.update({"delivery": cache_data["delivery"]})
        await asyncio.sleep(uniform(0.150, 0.350))

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
            if fetch_result["delivery"] == "auto":
                for msg in fetch_result["items"]:
                    await TelegramSender.send(target_id, msg)
            else:
                await bot.send_message(
                    user_id,
                    f"wall_id {wall_id}\nРепост в telegram чат {target_id}\n"
                    f"Получено {len(fetch_result['items'])} новых постов, ваши действия?",
                    reply_markup=make_respond_kb(wall_id),
                )
        else:
            logger.warning("No data")


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

    def add_job(self, user_id: int, wall_id: int, target_id: int, timeout: int, fetch_count: int):
        job = self._get_job_by_id(user_id, wall_id, target_id)
        if not job:
            scheduler.add_job(
                self.fetch_public_wall,
                IntervalTrigger(minutes=timeout),
                args=(
                    user_id,
                    wall_id,
                    target_id,
                    fetch_count,
                ),
                id=f"{user_id}:{wall_id}:{target_id}",
                next_run_time=datetime.now(),
            )
        else:
            logger.warning("The task is already in progress")

    async def update_delivery_settings(self, user_id: int, wall_id: int, target_id: int, param: str):
        latest_data = await self._get_data_from_redis(user_id, wall_id, target_id)
        latest_data.update({"delivery": param})
        await self.redis.hset(
            f"{user_id}:cache",
            f"{wall_id}:{target_id}",
            json.dumps(latest_data, ensure_ascii=False).encode("utf-8"),
        )

        if param in ["now", "auto"]:
            for msg in latest_data["items"]:
                await asyncio.wait(
                    [TelegramSender.send(target_id, msg), bot.send_chat_action(user_id, "typing")]
                )
            if param == "now":
                await bot.send_message(user_id, "Готово, ждем новых обновлений", reply_markup=confirm_kb)

    async def remove_job(self, user_id: int, wall_id: int, target_id: int):
        job = self._get_job_by_id(user_id, wall_id, target_id)
        if job:
            scheduler.remove_job(job.id)
            await self.redis.hdel(f"{user_id}:cache", f"{wall_id}:{target_id}")
        else:
            logger.warning("No such task")

    def pause_job(self, user_id: int, wall_id: int, target_id: int):
        job = self._get_job_by_id(user_id, wall_id, target_id)
        if job:
            scheduler.pause_job(job.id)
        else:
            logger.warning("No such task")

    def continue_job(self, user_id: int, wall_id: int, target_id: int):
        job = self._get_job_by_id(user_id, wall_id, target_id)
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
