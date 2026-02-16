from aiogram import Router, types, F
from aiogram.filters import Command

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


@router.message()
async def echo_handler(message: types.Message):
    try:
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        await message.answer("Я пока понимаю только текст!")
