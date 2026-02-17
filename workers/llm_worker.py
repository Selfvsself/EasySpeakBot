import logging

from database.requests import log_message
from infrastructure.kafka import kafka_client
from infrastructure.topics import MESSAGES_TOPIC, RESPONSES_TOPIC
from utils.llm_client import get_llm_answer


async def answer_consumer_task() -> None:
    async for data in kafka_client.consume_topic(MESSAGES_TOPIC):
        user_id = data.get("user_id")
        text = data.get("text")

        if user_id is None or text is None:
            logging.warning("Skip invalid Kafka payload: %s", data)
            continue

        logging.info("Received request to LLM from %s: %s", user_id, text)
        ai_response = await get_llm_answer(text)

        await log_message(user_id=user_id, text=ai_response, username="assistant")
        logging.info("Received answer from LLM for %s: %s", user_id, ai_response)

        try:
            await kafka_client.send_message(
                RESPONSES_TOPIC,
                {"user_id": user_id, "text": ai_response},
            )
        except Exception:
            logging.exception("Ошибка при отправке ответа в Kafka")
