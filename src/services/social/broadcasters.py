import json
from typing import List, Optional
from datetime import datetime

from loguru import logger
from aiogram import Dispatcher
from apscheduler.job import Job
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, JobExecutionEvent
from aiogram.utils.executor import Executor
from aiogram.utils.exceptions import BotBlocked, ChatNotFound, ChatAdminRequired
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.utils import RedisPool, scheduler
from src.settings import VK_TOKEN, REDIS_URI, REDIS_DB_CACHE

from ..social.vk import VkFetch
from ..social.utils import TelegramSender


class VKBroadcaster(RedisPool, VkFetch):
    """"""

    def __init__(self, token: str, current_scheduler: AsyncIOScheduler):
        super(VKBroadcaster, self).__init__(REDIS_URI, REDIS_DB_CACHE)
        self.token = token
        self.scheduler = current_scheduler

    def event_listener(self, event: JobExecutionEvent):
        if not event.exception:
            current_job = scheduler.get_job(event.job_id)
            if current_job and current_job.name == "vk_fetch_wall":
                fetch_items, user_cache = event.retval, current_job.id.split(":")
                scheduler.add_job(
                    self.send_wall_data_to_telegram,
                    args=(fetch_items, user_cache),
                    name="send_vk_data_to_telegram",
                )

    async def _get_user_log_channel(self, user_id: int) -> Optional[dict]:
        redis_data = await self.redis.hget(f"{user_id}:cache", "telegram_logs", encoding="utf-8")
        return json.loads(redis_data) if redis_data else None

    async def _setup_user_cache(self, user_id: int, wall_id: int, to_chat_id: int):
        latest_data = await self._get_data_from_redis(user_id, wall_id, to_chat_id)
        if not latest_data:
            new_data = {"to_chat_id": to_chat_id, "delivery": "auto", "items": []}
            await self.redis.hset(
                f"{user_id}:cache",
                f"{wall_id}:{to_chat_id}",
                json.dumps(new_data, ensure_ascii=False).encode("utf-8"),
            )

    def _get_job_by_id(self, *args: int) -> Optional[Job]:
        return self.scheduler.get_job(f"{args[0]}:{args[1]}:{args[2]}")

    async def _get_data_from_redis(self, *args: int) -> Optional[dict]:
        """
        :param args: (user_id, from_wall, to_chat_id)
        :return:
        """
        redis_data = await self.redis.hget(f"{args[0]}:cache", f"{args[1]}:{args[2]}", encoding="utf-8")
        return json.loads(redis_data) if redis_data else None

    def is_wall_active(self, user_id: int, wall_id: int, to_chat_id: int) -> bool:
        job = self._get_job_by_id(user_id, wall_id, to_chat_id)
        return True if job else False

    async def update_log_channel(self, user_id: int, channel_id: int, enable: bool = False):
        await self.redis.hset(
            f"{user_id}:cache",
            "telegram_logs",
            json.dumps({"channel_id": channel_id, "enabled": enable}, ensure_ascii=False).encode("utf-8"),
        )

    async def is_user_logs_active(self, user_id: int) -> bool:
        channel = await self._get_user_log_channel(user_id)
        return True if channel["enabled"] else False

    def get_user_jobs(self, user_id: int) -> Optional[List[Job]]:
        job_list = self.scheduler.get_jobs()
        return [job for job in job_list if user_id == job.args[0]] if job_list else None

    async def start_fetch_wall(self, job_data: tuple):
        user_id, wall_id, to_chat_id, timeout, fetch_count = job_data
        await self._setup_user_cache(user_id, wall_id, to_chat_id)
        scheduler.add_job(
            self.fetch_public_wall,
            IntervalTrigger(seconds=timeout),
            args=(
                wall_id,
                fetch_count,
            ),
            name="vk_fetch_wall",
            id=f"{user_id}:{wall_id}:{to_chat_id}",
            replace_existing=True,
            next_run_time=datetime.now(),
        )

    async def remove_wall(self, user_id: int, wall_id: int, to_chat_id: int):
        job = self._get_job_by_id(user_id, wall_id, to_chat_id)
        await self.redis.hdel(f"{user_id}:cache", f"{wall_id}:{to_chat_id}")
        if job:
            scheduler.remove_job(job.id)
        else:
            logger.warning("No such task")

    def stop_fetch_wall(self, user_id: int, wall_id: int, to_chat_id: int):
        job = self._get_job_by_id(user_id, wall_id, to_chat_id)
        if job:
            scheduler.remove_job(job.id)
        else:
            logger.warning("No such task")

    async def send_wall_data_to_telegram(self, wall_fetch_items: list, user_cache: tuple):
        data_to_send = []
        cache_data = await self._get_data_from_redis(*user_cache)
        user_logs = await self._get_user_log_channel(user_cache[0])

        for item in wall_fetch_items:
            if item["post_id"] not in [record["post_id"] for record in cache_data["items"]]:
                data_to_send.append(item)

        if data_to_send:
            if cache_data["delivery"] == "auto":
                await TelegramSender.send_log_message(
                    user_logs,
                    f"стена вк {user_cache[1]}\nПолучено {len(data_to_send)} "
                    f"новых записей, отправляю в канал {user_cache[2]}",
                )
                for msg in data_to_send:
                    try:
                        await TelegramSender.send(cache_data["to_chat_id"], msg)
                    except (BotBlocked, ChatNotFound, ChatAdminRequired):
                        logger.error(f"{user_cache} - bot error")
                        await TelegramSender.send_log_message(
                            user_logs,
                            f"стена вк {user_cache[1]}\nНе могу отправить запись в канал {user_cache[2]}\n"
                            f"Убедитесь, что бот не заблокирован и имеет админ права группе/канале",
                        )
                    except Exception as err:
                        logger.error(f"{user_cache} - another error: {err}")

            cache_data.update({"items": data_to_send})
            await self.redis.hset(
                f"{user_cache[0]}:cache",
                f"{user_cache[1]}:{user_cache[2]}",
                json.dumps(cache_data, ensure_ascii=False).encode("utf-8"),
            )
        else:
            logger.warning(f"{user_cache[1]} not new records")
            await TelegramSender.send_log_message(user_logs, f"стена {user_cache[1]}\nНет новых постов")


vk_broadcaster = VKBroadcaster(VK_TOKEN, scheduler)
vk_broadcaster.scheduler.add_listener(vk_broadcaster.event_listener, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)


async def on_startup(dispatcher: Dispatcher):
    await vk_broadcaster.connect()
    logger.info("Start vk broadcaster")


async def on_shutdown(dispatcher: Dispatcher):
    await vk_broadcaster.disconnect()
    logger.info("Shutdown vk broadcaster")


def vk_broadcaster_setup(runner: Executor):
    runner.on_startup(on_startup)
    runner.on_shutdown(on_shutdown)
