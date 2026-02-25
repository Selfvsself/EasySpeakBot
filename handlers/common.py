import logging

from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.utils.markdown import hbold

from infrastructure.kafka import kafka_client
from infrastructure.topics import MESSAGES_TOPIC, RESPONSES_TOPIC

router = Router()


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
