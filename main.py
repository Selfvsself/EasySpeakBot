import asyncio
import logging

from database.engine import proceed_db
from handlers import common, start
from infrastructure.kafka import kafka_client
from infrastructure.topics import RESPONSES_TOPIC
from loader import bot, dp
from workers import llm_worker

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


async def answer_consumer_task() -> None:
    async for data in kafka_client.consume_topic(RESPONSES_TOPIC):
        user_id = data.get("user_id")
        text = data.get("text")

        if user_id is None or text is None:
            logging.warning("Skip invalid Kafka payload: %s", data)
            continue

        logging.info("Received message from %s: %s", user_id, text)
        try:
            await bot.send_message(chat_id=user_id, text=f"Ответ: {text}")
        except Exception:
            logging.exception("Ошибка при отправке сообщения пользователю %s", user_id)


async def main() -> None:
    await proceed_db()
    dp.include_routers(start.router, common.router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    asyncio.create_task(answer_consumer_task())
    asyncio.create_task(llm_worker.answer_consumer_task())

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
