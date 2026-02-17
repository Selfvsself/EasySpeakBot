from aiogram import Router, types
from aiogram.filters import Command
from aiogram.utils.markdown import hbold, hitalic

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_name = message.from_user.first_name

    welcome_text = (
        f"👋 {hbold(f'Hello, {user_name}!')}\n\n"
        f"I'm {hbold('Alex')}, your new English-speaking buddy from London. 🇬🇧\n\n"
        "I'm here to chat with you about anything — from the rainy British weather "
        "to the latest movies or your daily routine. "
        f"The best part? {hitalic('I will help you improve your English while we talk!')}\n\n"
        f"💡 {hbold('How it works:')}\n"
        "1. Just type anything in English (or any language, but I'll stick to English!).\n"
        "2. I'll reply like a real friend.\n"
        "3. If I spot a mistake, I'll add a friendly correction at the end.\n\n"
        "So, how's your day going? ☕️"
    )

    await message.answer(
        text=welcome_text,
        parse_mode="HTML"
    )
