import logging

from database.requests import log_message
from infrastructure.kafka import kafka_client
from utils.llm_client import get_llm_answer


async def answer_consumer_task():
    async for data in kafka_client.consume_answers("messages_topic"):
        user_id = data.get("user_id")
        text = data.get("text")
        logging.info(f"Received request to llm message from {user_id} message: {text}")
        ai_response = await get_llm_answer(text)
        await log_message(
            user_id=user_id,
            text=ai_response,
            username="assistant"
        )
        logging.info(f"Received answer from llm message from {user_id} message: {ai_response}")
        try:
            await kafka_client.send_log("responses_topic", {
                "user_id": data["user_id"],
                "text": ai_response
            })
        except Exception as e:
            logging.error(f"Ошибка при отправке: {e}")
