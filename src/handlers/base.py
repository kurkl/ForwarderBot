from loguru import logger
from aiogram import types

from src.bot import dp, bot, broadcaster
from src.settings import TG_ME, LOG_CHANNEL
from src.utils.keyboards import DefaultConstructor


@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    keyboard_markup = DefaultConstructor.create_kb(
        [{"text": "Run"}, {"text": "Stop"}, {"text": "Status"}, {"text": "Logs"}], [4]
    )
    await message.reply("Bot menu", reply_markup=keyboard_markup)


@dp.message_handler(lambda msg: msg.chat.id == TG_ME)
async def vk_parser_commands_handler(message: types.Message):
    btn_text = message.text
    logger.debug(f"Command {btn_text}")

    if btn_text == "Run":
        await broadcaster.start_broadcasting()
    elif btn_text == "Logs":
        log_channel = await bot.export_chat_invite_link(LOG_CHANNEL)
        await message.answer(f"Канал с логами: {log_channel}")
    elif btn_text == "Status":
        await message.answer(f"Парсер {broadcaster.get_status()}")
    elif btn_text == "Stop":
        await broadcaster.stop_broadcasting()
    else:
        await message.answer(f'Command "{message.text}" is incorrect, see /help')


@dp.errors_handler()
async def errors_handler(update: types.Update, exception: Exception):
    try:
        raise exception
    except Exception as ex:
        logger.exception(f"Cause exception {ex} in update {update}")
    return True
