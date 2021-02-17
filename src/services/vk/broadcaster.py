import json
import time
import asyncio
from random import uniform
from typing import Dict, List, Type, Union
from datetime import datetime, timedelta
from threading import Thread
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass

import uvloop
import tenacity
from loguru import logger
from aiovk.api import API
from aiovk.sessions import TokenSession

from src.utils import RedisPool

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def set_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


@dataclass
class Task:
    """
    Provides container for user coro-task
    """

    task_id: int
    sleep: int
    _timeout: datetime = None
    _status: str = "READY"

    def __repr__(self):
        return f"<Task (id={self.task_id}, sleep={self.sleep}m, status={self._status})>"

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
        self._timeout = datetime.now() + timedelta(minutes=self.sleep)
        self._status = "DONE"

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

    redis_uri: str
    redis_db: int = None
    token: str = None
    is_running: ContextVar = ContextVar("Run flag")

    def __post_init__(self):
        self._tasks_queue = asyncio.Queue()
        self.is_running.set(False)
        self.redis_pool = RedisPool(self.redis_uri, self.redis_db)

    def __repr__(self):
        return f"<VkBroadcaster (is_running={self.is_running}, tasks_count={self._tasks_queue.qsize()})>"

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
            received_records = await session.wall.get(owner_id=wall_id, count=2, v=5.126)

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

            result["items"].append(item)
        result.update({"execution_date": time.time(), "running_time": time.time() - start_time})
        json_result = json.dumps(result, ensure_ascii=False).encode("utf-8")
        await self.redis_pool.redis.lpush(key=f"user_id{target}_tasks", value=json_result)

    async def consume_queue(self):
        """
        Launch circular task queue, tasks are executed as soon as available
        TODO: add multi queues for different execution timeout
        :return:
        """
        await self._tasks_queue.put({"task": Task(0, -1, _status="INIT"), "payload": "None"})
        logger.info("Run task scheduler")
        try:
            await self.redis_pool.connect()
            self.is_running.set(True)
            while True:
                next_item: Dict[str, Union[Task, Type[dict]]] = await self._tasks_queue.get()
                if next_item["task"].ready:
                    await next_item["task"].execute(
                        func=self.fetch_public_vk_wall, payload=next_item["payload"]
                    )
                    logger.info(next_item)
                await self._tasks_queue.put(next_item)
                await asyncio.sleep(0.00001)
        except (asyncio.TimeoutError, asyncio.CancelledError) as err:
            logger.error(f"asyncio error: {err}")
        except Exception as err:
            logger.error(f"Another error: {err}")
        finally:
            logger.info("Close task scheduler")
            await self.redis_pool.disconnect()

    def add_task(self, task_id: int, sleep: int, targets: Dict[str, List[int]]):
        self._tasks_queue.put_nowait({"task": Task(task_id, sleep), "payload": targets})
        logger.info(f"Task {task_id} has been added")

    def remove_task(self, task: Task, timeout: int = None):
        raise NotImplemented


def get_vk_broadcaster(redis_uri: str, token: str, redis_db: int = 1) -> VkBroadcaster:
    """
    Creates an VkBroadcaster instance and runs it on a separate thread
    :return:
    """
    loop = asyncio.new_event_loop()
    t = Thread(target=set_loop, args=(loop,))
    t.start()
    broadcaster = VkBroadcaster(redis_uri=redis_uri, redis_db=redis_db, token=token)
    asyncio.run_coroutine_threadsafe(broadcaster.consume_queue(), loop)
    return broadcaster
