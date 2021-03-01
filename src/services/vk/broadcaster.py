import json
import asyncio
from datetime import datetime, timedelta
from threading import Thread, ThreadError
from contextvars import ContextVar
from dataclasses import dataclass

import uvloop
import aioredis
from loguru import logger

from src.utils import RedisPool
from src.settings import TIME_FORMAT

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def set_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def is_job_ready(job: dict) -> bool:
    if job["status"] != "pause" and datetime.now() >= datetime.strptime(job["timeout"], TIME_FORMAT):
        return True
    return False


def set_timeout(sleep: int) -> str:
    return (datetime.now() + timedelta(minutes=sleep)).strftime(TIME_FORMAT)


class TaskExecutor:
    @staticmethod
    async def execute(func: callable, payload: dict) -> bytes:
        """
        Simple executor to run multiple background tasks
        :param func: background callback
        :param payload: args for callback
        :return:
        """
        results = await asyncio.gather(
            *[asyncio.create_task(func(arg0, arg1)) for arg0, arg1 in payload.items()]
        )
        return json.dumps(results, ensure_ascii=False).encode("utf-8")


@dataclass
class VkBroadcaster:
    """
    Receives data from one or multiple walls and publish it
    """

    redis_uri: str
    token: str
    redis_db: int
    is_running: ContextVar = ContextVar("Run flag")
    redis: aioredis.Redis = None

    def __post_init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = Thread(target=set_loop, name="consumer", args=(self._loop,))
        self._redis_pool = RedisPool(self.redis_uri, self.redis_db)

    def run(self):
        try:
            self.is_running.set(True)
            self._thread.start()
            asyncio.run_coroutine_threadsafe(self.consume_queue(), self._loop)
            logger.info("Run task queue consumer")
        except KeyboardInterrupt:
            logger.warning("User close process")
        except ThreadError:
            logger.error("Thread error")
        except Exception as err:
            logger.error(f"Another error: {err}")
        finally:
            logger.warning("Shutdown")

    async def init_redis(self):
        if self.redis:
            return
        await self._redis_pool.connect()
        self.redis = self._redis_pool.redis

    async def consume_queue(self):
        """
        Launch circular task queue, tasks are executed as soon as available
        TODO: add multi queues for different execution timeout
        :return:
        """
        try:
            while True:
                next_item = await self.redis.rpop("main_queue")
                if next_item:
                    job = json.loads(next_item)
                    # if is_job_ready(job):
                    #     job_result = await TaskExecutor.execute(
                    #         func=self.fetch_public_vk_wall, payload={job["source_id"]: job["to_channel"]}
                    #     )
                    #     job.update({"status": "timeout", "timeout": set_timeout(job["sleep"])})
                    #     await self.redis.xadd("main_stream", {"received_data": job_result})
                    #     logger.info(f"{job['user_id']} executed")
                    #     next_item = json.dumps(job)
                await self.redis.rpush("main_queue", next_item)
                await asyncio.sleep(0.00001)
        except (asyncio.TimeoutError, asyncio.CancelledError) as err:
            logger.error(f"asyncio error: {err}")
        except Exception as err:
            logger.error(f"Another error: {err}")
        finally:
            logger.info("Close redis pool")
            await self._redis_pool.disconnect()

    async def add_job(self, user_id: int, source_id: int, sleep: int, to_channel: int):
        params = {
            "user_id": user_id,
            "source_id": source_id,
            "to_channel": to_channel,
            "sleep": sleep,
            "status": "ready",
            "timeout_dt": datetime.now().strftime(TIME_FORMAT),
        }
        await self.redis.lpush("main_queue", json.dumps(params))
        logger.info(f"New task by user_id {user_id} has been added")

    async def remove_job(self, user_id: int, source_id: int):
        cap = await self.redis.llen("main_queue")
        flag = False
        full_job_list = await self.redis.lrange("main_queue", 0, cap, encoding="utf-8")
        for item in full_job_list:
            job = json.loads(item)
            if f"{job['user_id']}:{job['source_id']}" == f"{user_id}:{source_id}":
                flag = True
                await self.redis.lrem("main_queue", 0, item)
        if flag:
            logger.info(f"User task {user_id} has been deleted")
        else:
            logger.warning(f"User task {user_id} not found")

    async def pause_job(self, user_id: int, source_id: int):
        pass

    async def continue_job(self):
        pass
