import logging
import re

from infrastructure.kafka import kafka_client
from infrastructure.topics import RESPONSES_TOPIC
from loader import bot


def escape_markdown_v2(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'([\[\]()~`>#+\-=|{}.!])', r'\\\1', text)


async def answer_consumer_task() -> None:
    async for data in kafka_client.consume_topic(RESPONSES_TOPIC):
        user_id = data.get("user_id")
        response_msg = escape_markdown_v2(data.get("response_msg"))

        if user_id is None:
            logging.warning("Skip invalid Kafka payload: %s", data)
            continue

        try:
            if response_msg:
                await bot.send_message(chat_id=user_id, text=response_msg)
                logging.info("Send message to %s: %s", user_id, response_msg)
        except Exception:
            logging.exception("Error sending message to user %s", user_id)
