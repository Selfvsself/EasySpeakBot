from aiogram import Router, types, F
from aiogram.filters import Command

from database.requests import log_message

router = Router()


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    await message.answer(
        "Я — универсальный бот.\n"
        "Доступные команды:\n"
        "/start - запустить бота\n"
        "/help - эта справка"
    )


@router.message(F.text.lower() == "как дела?")
async def how_are_you(message: types.Message):
    await message.reply("Отлично! Работаю над твоим проектом 🤖")


@router.message(F.text)
async def echo_handler(message: types.Message):
    await log_message(
        user_id=message.from_user.id,
        text=message.text,
        username=message.from_user.username
    )
    await message.send_copy(chat_id=message.chat.id)


@router.message()
async def non_text_handler(message: types.Message):
    await message.answer("Я пока понимаю только текст!")
