import logging

from aiogram import F, Router, types
from aiogram.utils.markdown import hbold

from infrastructure.kafka import kafka_client
from infrastructure.topics import MESSAGES_TOPIC
from workers.bot_actions import ANSWER

router = Router()


@router.message(F.text)
async def text_message_handler(message: types.Message) -> None:
    if message.from_user is None or message.text is None:
        logging.warning("Skip message without text or user: %s", message)
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    await kafka_client.send_message(
        MESSAGES_TOPIC,
        {
            "app": "easy_speak_bot",
            "user_id": message.from_user.id,
            "user_name": message.from_user.username,
            "action": ANSWER,
            "text": message.text
        },
    )
    logging.info("Send message to %s: %s", message.from_user.id, message.text)


@router.message()
async def non_text_handler(message: types.Message) -> None:
    warning_text = (
        f"Sorry, mate! 😅 I can only understand {hbold('text messages')} for now.\n\n"
        "Could you please type your message in English? "
        "It's the best way to practice! ✍️🇬🇧"
    )

    await message.reply(
        text=warning_text
    )
