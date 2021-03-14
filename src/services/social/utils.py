from typing import Dict, List, Union
from datetime import datetime

from aiogram.types import InputMediaPhoto, InputMediaVideo

from runner import bot
from settings import TIME_FORMAT


class TelegramSender:
    @classmethod
    def prepare_message(cls, msg_data: dict) -> Dict[str, Union[list, dict, bool]]:
        """
        TODO: check if items len > 10
        FIXME: photo with video not sending
        :param msg_data:
        :return:
        """
        media_message = {"text": None, "has_poll": False, "media_data": []}
        media, text_message = msg_data.get("media"), msg_data.get("text")
        if text_message:
            media_message.update({"text": text_message})
        if media:
            if "videos" in media:
                # media_message["media_data"].extend([InputMediaVideo(video) for video in media["videos"]])
                return None
            if "photos" in media:
                media_message["media_data"].extend([InputMediaPhoto(photo) for photo in media["photos"]])
            if "poll" in media:
                media_message.update({"has_poll": True, "poll_data": dict(media["poll"])})
            if media_message["media_data"]:
                media_message["media_data"][0].caption = text_message
        return media_message

    @classmethod
    async def send(cls, chat_id: int, raw_message: dict):
        """
        Sends a message with or without attachments
        :param chat_id: telegram channel id
        :param raw_message: A JSON-serialized array with describing items to be sent
        """
        message = cls.prepare_message(raw_message)
        if not message:
            raise ValueError
        if message["has_poll"]:
            poll_data = message["poll_data"]
            answers = [answer["text"] for answer in poll_data["answers"]]
            if message["media_data"]:
                sent = await bot.send_media_group(chat_id=chat_id, media=message["media_data"])
                await bot.send_poll(
                    chat_id=chat_id,
                    question=poll_data["question"],
                    options=answers,
                    reply_to_message_id=sent.message_id,
                )
            else:
                sent = await bot.send_message(chat_id=chat_id, text=message["text"])
                await bot.send_poll(
                    chat_id=chat_id,
                    question=poll_data["question"],
                    options=answers,
                    reply_to_message_id=sent.message_id,
                )
        else:
            if message["media_data"]:
                await bot.send_media_group(chat_id=chat_id, media=message["media_data"])
            else:
                await bot.send_message(chat_id=chat_id, text=message["text"])

    @classmethod
    async def send_log_message(cls, user_logs: dict, message_text: str):
        if user_logs and user_logs["enabled"]:
            await bot.send_message(
                chat_id=user_logs["channel_id"],
                text=f"{datetime.now().strftime(TIME_FORMAT)} - {message_text}",
            )
