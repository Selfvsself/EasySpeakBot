import logging

from aiogram import F
from aiogram import Router, types
from aiogram.filters import Command

from infrastructure.kafka import kafka_client
from infrastructure.topics import RESPONSES_TOPIC, MESSAGES_TOPIC
from workers.bot_actions import TRANSLATE, CORRECTION

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


@router.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    help_text = (
        f"🇬🇧 *Cheers! I am Alex, your London buddy.*\n\n"
        "I'm here to help you practice your English in a natural way. "
        "Just send me a message, and let's chat! ☕️\n\n"
        f"*Available commands:*\n"
        f"/*start* — Start our conversation\n"
        f"/*help* — Show this info\n\n"
        f"_Note: I will always reply in English to help you learn faster. _"
        "If you make a mistake, I'll gently point it out at the end of my message. 😉"
    )

    await kafka_client.send_message(
        RESPONSES_TOPIC,
        {
            "app": "easy_speak_bot",
            "user_id": message.from_user.id,
            "user_name": message.from_user.username,
            "text": help_text
        },
    )
    logging.info("Send message to %s: %s", message.from_user.id, message.text)


@router.message(F.text.regexp(r'^/(\d+)$'))
async def handle_id_command(message: types.Message):
    if message.from_user is None or message.text is None:
        logging.warning("Skip message without text or user: %s", message)
        return

    action = message.text[-1]
    msg_id = int(message.text[1:-1])

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    await kafka_client.send_message(
        MESSAGES_TOPIC,
        {
            "app": "easy_speak_bot",
            "user_id": message.from_user.id,
            "user_name": message.from_user.username,
            "action": action,
            "msg_id": msg_id
        },
    )
    logging.info("Send message to %s: %s", message.from_user.id, message.text)
