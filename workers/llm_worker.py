import logging

from langchain_core.messages import HumanMessage, AIMessage

from database.messages_requests import save_message, get_unsummarized_messages, mark_messages_as_summarized
from database.users_requests import get_user_profile, update_user_profile
from infrastructure.kafka import kafka_client
from infrastructure.topics import MESSAGES_TOPIC, RESPONSES_TOPIC
from utils.llm_client import get_llm_answer, check_errors_with_llm, update_bio_with_llm, update_summary_with_llm, \
    get_translation_with_llm


async def answer_consumer_task() -> None:
    async for data in kafka_client.consume_topic(MESSAGES_TOPIC):
        user_id = data.get("user_id")
        user_name = data.get("user_name")
        text = data.get("text")
        application = data.get("app")

        if not application == "easy_speak_bot":
            continue

        if user_id is None or text is None:
            logging.warning("Skip invalid Kafka payload: %s", data)
            continue

        logging.info("Received request to LLM from %s: %s", user_id, text)
        profile = await get_user_profile(user_id)

        langchain_history = []
        if profile.summary:
            langchain_history.append(HumanMessage(content=f"Context of previous conversations: {profile.summary}"))
            langchain_history.append(AIMessage(content="Got it, I remember our previous talks."))

        db_history = await get_unsummarized_messages(user_id)
        for msg in db_history:
            if msg.username == "assistant":
                langchain_history.append(AIMessage(content=msg.text))
            else:
                langchain_history.append(HumanMessage(content=msg.text))

        await save_message(user_id=user_id, text=text, username=user_name)
        ai_response = await get_llm_answer(
            text,
            history=langchain_history,
            bio_data=profile.bio_data
        )
        ai_translation = await get_translation_with_llm(ai_response)
        ai_correction = ""
        if db_history:
            ai_correction = await check_errors_with_llm(
                db_history[-1].text,
                text
            )

        await save_message(user_id=user_id, text=ai_response, username="assistant")
        logging.info("Received answer from LLM for %s: %s", user_id, ai_response)

        try:
            await kafka_client.send_message(
                RESPONSES_TOPIC,
                {"user_id": user_id,
                 "text": ai_response,
                 "translation": ai_translation,
                 "corrections": ai_correction},
            )
        except Exception:
            logging.exception("Error sending response to Kafka")

        if len(db_history) > 15:
            to_process = db_history[:-10]
            new_text_block = ""
            for m in to_process:
                role = "ai assistant"
                if not m.username == "assistant":
                    role = "user"
                text = m.text.replace("\n", " ")
                new_text_block += f"{role}: '{text}'\n"

            new_bio = await update_bio_with_llm(profile.bio_data, new_text_block)
            new_summary = await update_summary_with_llm(str(profile.summary), new_text_block)

            await update_user_profile(user_id, summary=new_summary, bio_updates=new_bio)
            await mark_messages_as_summarized([m.id for m in to_process])

            logging.info("Archived %s messages for user %s", len(to_process), user_id)
