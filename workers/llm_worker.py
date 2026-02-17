import logging

from langchain_core.messages import HumanMessage, AIMessage

from database.requests import save_message, get_recent_messages
from infrastructure.kafka import kafka_client
from infrastructure.topics import MESSAGES_TOPIC, RESPONSES_TOPIC
from utils.llm_client import get_llm_answer


async def answer_consumer_task() -> None:
    async for data in kafka_client.consume_topic(MESSAGES_TOPIC):
        user_id = data.get("user_id")
        user_name = data.get("user_name")
        text = data.get("text")

        if user_id is None or text is None:
            logging.warning("Skip invalid Kafka payload: %s", data)
            continue

        logging.info("Received request to LLM from %s: %s", user_id, text)
        db_history = await get_recent_messages(user_id, limit=10)
        langchain_history = []
        for msg in db_history:
            if msg.username == "assistant":
                langchain_history.append(AIMessage(content=msg.text))
            else:
                langchain_history.append(HumanMessage(content=msg.text))

        await save_message(user_id=user_id, text=text, username=user_name)

        ai_response = await get_llm_answer(text, history=langchain_history)

        await save_message(user_id=user_id, text=ai_response, username="assistant")
        logging.info("Received answer from LLM for %s: %s", user_id, ai_response)

        try:
            await kafka_client.send_message(
                RESPONSES_TOPIC,
                {"user_id": user_id, "text": ai_response},
            )
        except Exception:
            logging.exception("Error sending response to Kafka")
