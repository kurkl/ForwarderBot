import json
import time
import asyncio
from random import uniform
from typing import Dict, List, Type, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from asyncio.queues import Queue

import uvloop
import tenacity
from loguru import logger
from aiovk.api import API
from aiovk.sessions import TokenSession

from src.utils import RedisPool

# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


@dataclass
class Task:
    """
    Provides container for user coro-task
    """

    task_id: int
    sleep: int
    _end_time: datetime = None
    _timeout: datetime = None
    _status: str = "READY"

    def __repr__(self):
        return f"<Task (id={self.task_id}, status={self._status})>"

    async def execute(self, func: callable, payload=dict):
        """
        Simple executor to run multiple background tasks
        :param func: background callback
        :param payload: args for callback
        :return:
        """
        results = [
            asyncio.ensure_future(func(wall_id, target_id))
            for wall_id, target_id in zip(payload["wall_ids"], payload["targets"])
        ]
        jobs = asyncio.wait(results)
        await jobs
        self._end_time = datetime.now()
        self._timeout = self._end_time + timedelta(minutes=self.sleep)

    def _get_status(self):
        if not self._timeout:
            return self._status
        now = datetime.now()
        if now <= self._timeout:
            self._status = "TIMEOUT"
        elif now >= self._timeout:
            self._status = "READY"
        else:
            self._status = "CANCELLED"

    def _change_status(self, value: str):
        self._status = value

    @property
    def ready(self) -> bool:
        self._get_status()
        return self._status == "READY"


@dataclass
class VkBroadcaster:
    """
    Receives data from one or multiple walls and publish it
    """

    token: str = None
    loop: asyncio.AbstractEventLoop = None
    redis_pool: RedisPool = None
    redis_channels: List[str] = None
    is_running: ContextVar = ContextVar("Run flag")

    def __post_init__(self):
        self._tasks_queue = Queue()
        self.is_running.set(False)
        self.redis_channels = ["main_channel:1"]

    async def init_redis(self):
        await self.redis_pool.connect()

    def __await__(self):
        return self.init_redis().__await__()

    def __repr__(self):
        return f"<VkBroadcaster (is_running={self.is_running}, tasks_count={self._tasks_queue.qsize()})>"

    def run(self, loop: asyncio.AbstractEventLoop = None):
        if loop:
            self.loop = loop
        else:
            self.loop = asyncio.get_event_loop()

        try:
            self.is_running.set(True)
            self.loop.run_until_complete(self.run_task_queue())
        finally:
            logger.info("Shutting down")

    @asynccontextmanager
    async def _session_scope(self):
        session = TokenSession(access_token=self.token)
        try:
            yield API(session)
        except Exception as err:
            logger.error(f"Error: {err}")
            raise
        finally:
            await session.close()

    @tenacity.retry(wait=tenacity.wait_fixed(2), stop=tenacity.stop_after_attempt(2))
    async def fetch_public_vk_wall(self, wall_id: int, target: int):
        """
        Get public vk data with wall.get method
        :param wall_id:
        :param target: telegram id channel, group or user id
        :return: saves the received data in the redis channel for further processing
        """
        await asyncio.sleep(uniform(0.150, 0.350))
        start_time = time.time()

        result = {"target_id": target, "items": []}
        async with self._session_scope() as session:
            received_records = await session.wall.get(owner_id=wall_id, count=10, v=5.126)

        for record in received_records["items"][1:]:
            item = {}
            item.update({"date": datetime.fromtimestamp(record["date"])})
            if "text" in record:
                item.update({"text": record["text"]})

            if "attachments" in record:
                item.update({"media": {"photos": [], "videos": [], "audio": [], "polls": []}})
                for attach in record["attachments"]:
                    if attach["type"] == "photo":
                        item["media"]["photos"].append(attach["photo"]["sizes"][-1]["url"])
                    # TODO: get video, polls, voice etc

            result["items"].append(item)
        result.update({"execution_date": datetime.now(), "running_time": time.time() - start_time})
        json_result = json.dumps(result, indent=4, default=str)
        await self.redis_pool.redis.publish_json(*self.redis_channels, json_result)

    async def run_task_queue(self):
        """
        Launch circular task queue, tasks are executed as soon as available
        TODO: add multi queues for different execution timeout
        :return:
        """
        try:
            await self.redis_pool.redis.subscribe(*self.redis_channels)
            while True:
                next_item: Dict[str, Union[Task, Type[dict]]] = await self._tasks_queue.get()
                # logger.info(f"{next_item}")
                if next_item["task"].ready:
                    await next_item["task"].execute(
                        func=self.fetch_public_vk_wall, payload=next_item["payload"]
                    )
                    await self._tasks_queue.put(next_item)
                else:
                    await self._tasks_queue.put(next_item)
                await asyncio.sleep(0.5)
        except (asyncio.CancelledError, asyncio.TimeoutError) as err:
            logger.error(f"asyncio error: {err}")
        except Exception as err:
            logger.error(f"Another error: {err}")

    def add_task(self, task_id: int, sleep: int, targets: Dict[str, List[int]]):
        self._tasks_queue.put_nowait({"task": Task(task_id, sleep), "payload": targets})
        logger.info(f"Task {task_id} has been added")

    def remove_task(self, task: Task):
        raise NotImplemented

    def pause_task(self, task: Task, timeout: int = None):
        raise NotImplemented


def vk_broadcaster(redis_uri: str, token: str, store: int = 1) -> VkBroadcaster:
    return VkBroadcaster(token=token, redis_pool=RedisPool(redis_uri, store))
