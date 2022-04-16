import logging

from aiogram import Bot, Dispatcher
from aiohttp import web
from sqlalchemy.ext.asyncio import create_async_engine
from aiogram.dispatcher.fsm.storage.redis import RedisStorage
from aiogram.dispatcher.webhook.aiohttp_server import SimpleRequestHandler

from config import settings, setup_logging
from handlers import system
from middleware import DBSessionMiddleware

setup_logging()

logger = logging.getLogger(__name__)

bot = Bot(token=settings.TG_BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=RedisStorage.from_url(settings.REDIS_BASE_URI))
engine = create_async_engine(settings.SQLALCHEMY_DB_URI, echo=True)


async def on_startup_webhook(app: web.Application):
    logger.info(f"Configure Web-Hook URL to: {settings.WEBHOOK_URL}")
    await bot.set_webhook(
        url=settings.WEBHOOK_URL,
        drop_pending_updates=True,
        allowed_updates=dp.resolve_used_update_types(),
    )


async def on_shutdown_webhook(app: web.Application):
    logger.info("Shutdown bot")
    await bot.session.close()


async def create_bot_app() -> web.Application:
    app = web.Application()

    # Register middlewares
    dp.message.middleware(DBSessionMiddleware(engine))
    dp.callback_query.middleware(DBSessionMiddleware(engine))

    # Register handlers
    dp.include_router(system.router)

    app.on_startup.append(on_startup_webhook)
    app.on_shutdown.append(on_shutdown_webhook)
    SimpleRequestHandler(dp, bot).register(app, settings.WEBHOOK_PATH)

    return app


if __name__ == "__main__":
    web.run_app(create_bot_app(), host="localhost", port=80)
