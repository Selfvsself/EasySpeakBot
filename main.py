import asyncio
import logging

from database.engine import proceed_db
from handlers import start, common
from infrastructure.kafka import kafka_client
from loader import bot, dp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


async def on_startup():
    await kafka_client.start()
    logging.info("Kafka producer started")


async def on_shutdown():
    await kafka_client.stop()
    logging.info("Kafka producer stopped")


async def answer_consumer_task():
    async for data in kafka_client.consume_answers("messages_topic"):
        user_id = data.get("user_id")
        text = data.get("text")
        logging.info(f"Received message from {user_id} message: {text}")
        try:
            await bot.send_message(chat_id=user_id, text=f"Ответ: {text}")
        except Exception as e:
            logging.error(f"Ошибка при отправке: {e}")


async def main():
    await proceed_db()
    dp.include_routers(start.router, common.router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    asyncio.create_task(answer_consumer_task())

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
