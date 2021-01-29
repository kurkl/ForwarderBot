import sys
import asyncio

from loguru import logger
from aiogram import Bot, Dispatcher, types, executor
from aiovk.api import API
from aiovk.sessions import ImplicitSession

from app.settings import (
    TG_ME,
    VK_PASS,
    VK_LOGIN,
    VK_APP_ID,
    VK_WALL_ID,
    LOG_CHANNEL,
    TG_BOT_TOKEN,
    TARGET_CHANNEL,
)

logger.add(sys.stdout, level="INFO", format="{time} - {name} - {level} - {message}")

bot = Bot(token=TG_BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot=bot)
parser_task = asyncio.Future()


async def start_parsing(delay: int) -> None:
    current_post = ""
    while True:
        received_post = await fetch_vk_wall(VK_WALL_ID)

        if not received_post["text"]:
            await bot.send_message(LOG_CHANNEL, "Skip post")
        else:
            if received_post["text"] != current_post:
                current_post = received_post["text"]

                if "media" in received_post:

                    if received_post["media"]:
                        attach = types.MediaGroup()
                        media = received_post["media"]
                        caption = received_post["text"]

                        if media["photo"]:
                            attach.attach_photo(
                                media["photo"][0],
                                caption=caption,
                            )
                            if len(media["photo"]) > 1:
                                for photo in media["photo"][1:]:
                                    attach.attach_photo(photo)

                        if media["video"]:
                            if len(received_post["media"]["video"]) > 1:
                                for video in received_post["media"]["video"][1:]:
                                    attach.attach_video(video)
                            else:
                                if len(media["photo"]) == 0:
                                    attach.attach_video(
                                        media["video"][0],
                                        caption=caption,
                                    )
                                else:
                                    attach.attach_video(media["video"][0])

                        try:
                            await bot.send_media_group(TARGET_CHANNEL, attach)
                        except Exception as err:
                            logger.info(err)
                            await bot.send_message(LOG_CHANNEL, "Skip post")
                            # continue
                else:
                    await bot.send_message(TARGET_CHANNEL, received_post["text"])
            else:
                await bot.send_message(LOG_CHANNEL, "Новых постов нет")

        await asyncio.sleep(delay)


def is_parser_running(task: asyncio.Future) -> bool:
    return True if task in asyncio.all_tasks() else False


async def fetch_vk_wall(wall_id: int) -> dict:
    async with ImplicitSession(VK_LOGIN, VK_PASS, VK_APP_ID) as session:
        api = API(session)
        try:
            data = await api.wall.get(owner_id=wall_id, count=2)
            record = data["items"][1]
        except Exception as err:
            logger.error(err)
        else:
            if "text" not in record:
                return {"text": ""}

            if "attachments" in record:
                media_urls = {"photo": [], "video": []}

                for attach in record["attachments"]:
                    if attach["type"] == "photo":
                        media_urls["photo"].append(attach["photo"]["photo_2560"])

                return {"text": record["text"], "media": media_urls}
            else:
                return {"text": record["text"]}


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    keyboard_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btns_text = ("Run", "Stop", "Status", "Logs")
    keyboard_markup.row(*(types.KeyboardButton(text) for text in btns_text))
    await message.reply("Bot menu", reply_markup=keyboard_markup)


@dp.message_handler(lambda msg: msg.chat.id == TG_ME)
async def commands_handler(message: types.Message):
    global parser_task
    btn_text = message.text
    logger.debug(f"Command {btn_text}")

    if btn_text == "Run":
        if not is_parser_running(parser_task):
            parser_task = asyncio.create_task(start_parsing(1))
            logger.info(parser_task.current_task())
            parser_state = f"Начинаем парсинг контента wall_id: {VK_WALL_ID}"
            await parser_task
        else:
            parser_state = "Парсер уже запущен"
    elif btn_text == "Logs":
        log_channel = await bot.export_chat_invite_link(LOG_CHANNEL)
        parser_state = f"Канал с логами: {log_channel}"
    elif btn_text == "Status":
        if is_parser_running(parser_task):
            parser_state = f"Парсер работает wall_id {VK_WALL_ID}"
            logger.info(parser_task.current_task())
        else:
            parser_state = "Парсер выключен"
    elif btn_text == "Stop":
        if is_parser_running(parser_task):
            parser_task.cancel()
            logger.info(parser_task.current_task())
            parser_state = f"Останавливаем парсинг wall_id: {VK_WALL_ID}"
        else:
            parser_state = "Парсер уже остановлен"
    else:
        parser_state = f'Command "{message.text}" is incorrect, see /help'

    await message.reply(parser_state)


def run_bot_polling():
    executor.start_polling(dp, skip_updates=True)
