import asyncio
import logging

from database.engine import proceed_db
from handlers import start, common
from loader import bot, dp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


async def main():
    await proceed_db()
    dp.include_routers(start.router, common.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
