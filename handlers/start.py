import logging

from aiogram import Router, types
from aiogram.filters import Command

from infrastructure.kafka import kafka_client
from infrastructure.topics import RESPONSES_TOPIC

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_name = message.from_user.first_name

    welcome_text = (
        f"👋 *Hello, {user_name}!*\n\n"
        f"I'm *Alex*, your new English-speaking buddy from London. 🇬🇧\n\n"
        "I'm here to chat with you about anything — from the rainy British weather "
        "to the latest movies or your daily routine. "
        f"The best part? _I will help you improve your English while we talk!_\n\n"
        f"💡 *How it works:*\n"
        "1. Just type anything in English (or any language, but I'll stick to English!).\n"
        "2. I'll reply like a real friend.\n"
        "3. If I spot a mistake, I'll add a friendly correction at the end.\n\n"
        "So, how's your day going? ☕️"
    )

    await kafka_client.send_message(
        RESPONSES_TOPIC,
        {
            "app": "easy_speak_bot",
            "user_id": message.from_user.id,
            "user_name": message.from_user.username,
            "text": welcome_text
        },
    )
    logging.info("Send message to %s: %s", message.from_user.id, message.text)
