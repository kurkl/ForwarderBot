import sys
import asyncio

import vk_api
from loguru import logger
from aiogram import Bot, Dispatcher, types, executor

from app.settings import TG_ME, VK_PASS, VK_LOGIN, VK_WALL_ID, TG_BOT_TOKEN, TARGET_CHANNEL

logger.add(sys.stdout, level="INFO", format="{time} - {name} - {level} - {message}")

bot = Bot(token=TG_BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot=bot)


async def start_parsing(delay: int):
    current_post = ""
    while True:
        received_post = get_last_posts_from_vk(VK_WALL_ID)

        if not received_post["text"]:
            await bot.send_message(TG_ME, "Skip post")
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
                            await bot.send_message(TG_ME, "Skip post")
                            # continue
                else:
                    await bot.send_message(TARGET_CHANNEL, received_post["text"])
            else:
                await bot.send_message(TG_ME, "Новых постов нет")

        await asyncio.sleep(delay)


async def stop_parsing():
    pass


async def check_status():
    pass


def get_last_posts_from_vk(wall_id: int) -> dict:
    vk_session = vk_api.VkApi(VK_LOGIN, VK_PASS)

    try:
        vk_session.auth(token_only=True)
    except vk_api.AuthError as error_msg:
        logger.error(error_msg)
        return

    vk = vk_session.get_api()

    data = vk.wall.get(owner_id=wall_id, count=2)["items"][1]

    if "text" not in data:
        return {"text": ""}

    if "attachments" in data:
        media_urls = {"photo": [], "video": []}

        for attach in data["attachments"]:
            if attach["type"] == "photo":
                media_urls["photo"].append(attach["photo"]["sizes"][-1]["url"])

        return {"text": data["text"], "media": media_urls}
    else:
        return {"text": data["text"]}


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    keyboard_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btns_text = ("Run parse", "Stop", "Check status", "Help")
    keyboard_markup.row(*(types.KeyboardButton(text) for text in btns_text))
    await message.reply("Starting", reply_markup=keyboard_markup)


@dp.message_handler(lambda msg: msg.chat.id == TG_ME)
async def commands_handler(message: types.Message):
    btn_text = message.text
    logger.debug(f"Command {btn_text}")

    if btn_text == "Run parse":
        await start_parsing(300)
    elif btn_text == "Check status":
        await check_status()
    elif btn_text == "Stop":
        await stop_parsing()
    elif btn_text == "Help":
        await message.reply("Доступные команды:\n")
    else:
        await message.reply("Error")


def run_bot_polling():
    executor.start_polling(dp, skip_updates=True)
