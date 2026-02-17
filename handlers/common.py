import logging

from aiogram import F, Router, types
from aiogram.filters import Command

from database.requests import log_message
from infrastructure.kafka import kafka_client
from infrastructure.topics import MESSAGES_TOPIC

router = Router()


@router.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    await message.answer(
        "Я — универсальный бот.\n"
        "Доступные команды:\n"
        "/start - запустить бота\n"
        "/help - эта справка"
    )


@router.message(F.text.lower() == "как дела?")
async def how_are_you(message: types.Message) -> None:
    await message.reply("Отлично! Работаю над твоим проектом 🤖")


@router.message(F.text)
async def echo_handler(message: types.Message) -> None:
    if message.from_user is None or message.text is None:
        logging.warning("Skip message without text or user: %s", message)
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    await log_message(
        user_id=message.from_user.id,
        text=message.text,
        username=message.from_user.username,
    )
    await kafka_client.send_message(
        MESSAGES_TOPIC,
        {
            "user_id": message.from_user.id,
            "text": message.text,
        },
    )
    logging.info("Send message to %s: %s", message.from_user.id, message.text)


@router.message()
async def non_text_handler(message: types.Message) -> None:
    await message.answer("Я пока понимаю только текст!")
