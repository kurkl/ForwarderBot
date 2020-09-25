import os
import asyncio
import logging
from pathlib import Path

import vk_api
from dotenv import load_dotenv
from aiogram import Bot, types, executor
from aiogram import Dispatcher

env_path = Path(".env")
load_dotenv(env_path)

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# vk settings
VK_LOGIN = os.getenv("VK_LOGIN")
VK_PASS = os.getenv("VK_PASS")

# telegram settings
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")
TEST_CHANNEL = os.getenv("TEST_CHANNEL")
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")


bot = Bot(token=TG_BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot=bot)


async def start_parsing(delay: int):
    current_post = ""
    while True:
        received_post = get_last_posts_from_vk()

        if not received_post["text"]:
            await bot.send_message(356061169, "Skip post")

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
                        logger.warning(err)
                        await bot.send_message(356061169, "Skip post")
            else:
                await bot.send_message(TARGET_CHANNEL, received_post["text"])
        else:
            await bot.send_message(356061169, "Новых постов нет")

        await asyncio.sleep(delay)


def get_last_posts_from_vk() -> dict:
    vk_session = vk_api.VkApi(VK_LOGIN, VK_PASS)

    try:
        vk_session.auth(token_only=True)
    except vk_api.AuthError as error_msg:
        logger.info(error_msg)
        return

    vk = vk_session.get_api()

    data = vk.wall.get(owner_id=-173594906, count=2)["items"][1]

    if "text" not in data:
        return {"text": ""}

    # if __debug__:
    #     with open(Path("src/debug/wall_posts.json"), "w", encoding="utf-8") as file:
    #         json.dump(data, file, indent=4, ensure_ascii=False)

    if "attachments" in data:
        media_urls = {"photo": [], "video": []}

        for attach in data["attachments"]:
            if attach["type"] == "photo":
                media_urls["photo"].append(attach["photo"]["sizes"][-1]["url"])
            # if attach['type'] == 'video':
            #     # raw_vid = vk.video.get(owner_id=-173594906, videos=f"{attach['video']['owner_id']}_{attach['video']['id']}", v=5.122)
            #     media_urls['video'].append(f"https://vk.com/video{attach['video']['owner_id']}_{attach['video']['id']}")

        return {"text": data["text"], "media": media_urls}
    else:
        return {"text": data["text"]}


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    keyboard_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btns_text = ("Run parse", "Stop", "Check status", "Help")
    keyboard_markup.row(*(types.KeyboardButton(text) for text in btns_text))
    await message.reply("Starting", reply_markup=keyboard_markup)


@dp.message_handler(lambda msg: msg.chat.id == 356061169)
async def commands_handler(message: types.Message):
    btn_text = message.text
    logger.debug(f"Command {btn_text}")

    if btn_text == "Run parse":
        await start_parsing(300)
    elif btn_text == "Check status":
        pass
    elif btn_text == "Stop":
        pass
    elif btn_text == "Help":
        await message.reply("Доступные команды:\n")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
