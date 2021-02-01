import asyncio

from loguru import logger
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import Executor

from src.settings import TG_ME, VK_WALL_ID, LOG_CHANNEL, TG_BOT_TOKEN, TARGET_CHANNEL
from src.database.db import db_setup
from src.utils.logging import logging_setup

from .vk_parser import fetch_vk_wall, make_telegram_data_to_send

bot = Bot(token=TG_BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot=bot)
runner = Executor(dp, skip_updates=True)
parser_task = asyncio.Future()


async def start_parsing(delay: int) -> None:
    while True:
        received_record = await fetch_vk_wall(VK_WALL_ID)
        if received_record["text"] in ["null", "no updates"]:
            await bot.send_message(LOG_CHANNEL, received_record["text"])
        else:
            attach = make_telegram_data_to_send(received_record)
            if isinstance(attach, str):
                await bot.send_message(TARGET_CHANNEL, attach)
            else:
                await bot.send_media_group(TARGET_CHANNEL, attach)

        await asyncio.sleep(delay)


def is_parser_running(task: asyncio.Future) -> bool:
    return True if task in asyncio.all_tasks() else False


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
            parser_task = asyncio.create_task(start_parsing(300))
            logger.info(parser_task.current_task())
            parser_state = f"Начинаем парсинг контента wall_id: {VK_WALL_ID}"
            await parser_task
        else:
            parser_state = f"Парсер уже запущен wall_id: {VK_WALL_ID}"
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
    logging_setup()
    db_setup(runner)
    runner.start_polling()
