import logging

from infrastructure.kafka import kafka_client
from infrastructure.topics import RESPONSES_TOPIC
from loader import bot


async def answer_consumer_task() -> None:
    async for data in kafka_client.consume_topic(RESPONSES_TOPIC):
        user_id = data.get("user_id")
        text = data.get("text")

        if user_id is None or text is None:
            logging.warning("Skip invalid Kafka payload: %s", data)
            continue

        logging.info("Received message from %s: %s", user_id, text)
        try:
            await bot.send_message(chat_id=user_id, text=text)
        except Exception:
            logging.exception("Error sending message to user %s", user_id)
