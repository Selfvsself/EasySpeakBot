import asyncio
import logging

from database.engine import proceed_db
from handlers import common, start
from infrastructure.kafka import kafka_client
from loader import bot, dp
from workers import llm_worker, bot_responder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


async def on_startup() -> None:
    await kafka_client.start()
    logging.info("Kafka producer started")


async def on_shutdown() -> None:
    await kafka_client.stop()
    logging.info("Kafka producer stopped")


async def main() -> None:
    await proceed_db()
    dp.include_routers(start.router, common.router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    asyncio.create_task(bot_responder.answer_consumer_task())
    asyncio.create_task(llm_worker.answer_consumer_task())

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
