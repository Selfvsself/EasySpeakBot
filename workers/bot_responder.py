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
        text = escape_markdown_v2(data.get("text"))
        corrections = escape_markdown_v2(data.get("corrections"))
        translation = escape_markdown_v2(data.get("translation"))

        if user_id is None or text is None:
            logging.warning("Skip invalid Kafka payload: %s", data)
            continue

        try:
            await bot.send_message(chat_id=user_id, text=text)
            logging.info("Send message to %s: %s", user_id, text)
            if corrections:
                await bot.send_message(chat_id=user_id, text=f"*Quick English Note:*\n{corrections}")
                logging.info("Send message to %s: %s", user_id, corrections)
            if translation:
                await bot.send_message(chat_id=user_id, text=f"*Translation \(tap to see\):*\n||{translation}||")
                logging.info("Send message to %s: %s", user_id, translation)
        except Exception:
            logging.exception("Error sending message to user %s", user_id)
