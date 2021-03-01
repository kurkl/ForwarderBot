from aiogram import Dispatcher
from aiogram.utils.executor import Executor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.settings import REDIS_HOST, REDIS_PORT, REDIS_DB_JOBS, REDIS_PASSWORD

jobstores = {
    "default": RedisJobStore(db=REDIS_DB_JOBS, host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
}
executors = {
    "default": AsyncIOExecutor(),
}
job_defaults = {"coalesce": False, "max_instances": 3}

scheduler = AsyncIOScheduler(jobstorer=jobstores, executors=executors, job_defaults=job_defaults)


async def on_startup(dispatcher: Dispatcher):
    scheduler.start()


async def on_shutdown(dispatcher: Dispatcher):
    scheduler.shutdown()


def scheduler_setup(executor: Executor):
    executor.on_startup(on_startup)
    executor.on_shutdown(on_shutdown)
