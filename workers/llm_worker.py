import logging

from langchain_core.messages import HumanMessage, AIMessage

from database.messages_requests import (
    save_message,
    get_unsummarized_messages,
    get_message_by_id,
    mark_messages_as_summarized)
from database.models import UserProfile
from database.users_requests import get_user_profile, update_user_profile
from infrastructure.kafka import kafka_client
from infrastructure.topics import MESSAGES_TOPIC, RESPONSES_TOPIC
from utils.llm_client import (
    get_llm_answer,
    check_errors_with_llm,
    update_bio_with_llm,
    update_summary_with_llm,
    get_translation_with_llm,
    get_web_search_decision,
    get_web_search_summary)
from utils.web_search import duckduckgo_search, format_search_results
from workers.bot_actions import ANSWER, TRANSLATE, CORRECTION

error_text = (
    "Oh, bloody hell! 🤦‍♂️ Something went a bit wrong on my end, mate.\n\n"
    "It seems I've spilled my tea over the server! ☕️⚡️\n"
    "Could you please try sending your message again in a moment? "
    "I'll be back in tip-top shape shortly! 🇬🇧"
)

no_data_text = (
    "Blimey! 😲 You've caught me off guard there, mate.\n\n"
    "I've searched my brain (and my little London library), but I couldn't "
    "find anything on that. My apologies! 📚❌\n\n"
    "Could you try asking in a different way? Or maybe let's talk about "
    "something else, like your favourite English city? ☕️🇬🇧"
)
restricted_text = (
    "Cheers for the message, mate! Но, as we say in London, "
    "that's a bit of a tricky one. 😅\n\n"
    "I'm not quite sure how to answer that, or maybe it's a topic "
    "best discussed over a pint (which I can't do yet!). 🍺\n\n"
    "Let's stick to something else, shall we? Tell me about your hobbies "
    "or how your day is going! ✍️🇬🇧"
)


async def answer_consumer_task() -> None:
    async for data in kafka_client.consume_topic(MESSAGES_TOPIC):
        user_id = data.get("user_id")
        user_name = data.get("user_name")
        action = data.get("action")
        application = data.get("app")

        if not application == "easy_speak_bot":
            logging.warning("Skip invalid Kafka payload: %s, wrong application", data)
            continue

        if not action:
            logging.warning("Skip invalid Kafka payload: %s, wrong action", data)
            continue

        if user_id is None:
            logging.warning("Skip invalid Kafka payload: %s, wrong user_id", data)
            continue

        db_history = await get_unsummarized_messages(user_id)
        profile = await get_user_profile(user_id)

        action = int(action)

        response_msg = error_text

        if action == ANSWER:
            text = data.get("text")
            response_msg = await request_answer_from_llm(
                user_id = user_id,
                text = text,
                user_name = user_name,
                db_history = db_history,
                profile = profile
            )
        elif action == TRANSLATE:
            msg_id = data.get("msg_id")
            msg = await get_message_by_id(msg_id)
            if not msg:
                response_msg = error_text
            elif not user_id == msg.user_id:
                response_msg = restricted_text
            elif msg.is_summarized:
                response_msg = no_data_text
            else:
                response_msg = await get_translation_with_llm(msg.text)
                if response_msg:
                    response_msg = f"*Translation:*\n{response_msg}"
        elif action == CORRECTION:
            msg_id = data.get("msg_id")
            msg = await get_message_by_id(msg_id)
            if not msg:
                response_msg = error_text
            elif not user_id == msg.user_id:
                response_msg = restricted_text
            elif msg.is_summarized:
                response_msg = no_data_text
            else:
                response_msg = await get_correction_message(msg.text, db_history)
                if response_msg:
                    response_msg = f"*Quick English Note:*\n{response_msg}"

        try:
            await kafka_client.send_message(
                RESPONSES_TOPIC,
                {"user_id": user_id,
                 "response_msg": response_msg},
            )
        except Exception:
            logging.exception("Error sending response to Kafka")

        if len(db_history) > 15:
            await summarize_old_messages(user_id, db_history, profile)


async def get_correction_message(text: str, db_history: list = None) -> str:
    prev_message = ""
    if db_history:
        for i in range(len(db_history) - 1, -1, -1):
            if db_history[i].text == text:
                prev_message = db_history[i - 1].text
    return await check_errors_with_llm(
        text,
        prev_message
    )


async def get_search_decision(text: str, db_history: dict = None, bio_data: dict = None) -> dict:
    history_text = "\n".join([
        f"{'assistant' if msg.username == 'assistant' else 'user'}: {msg.text}"
        for msg in db_history
    ])
    return await get_web_search_decision(text, history_text=history_text, bio_data=bio_data)


async def get_answer_from_llm(text: str, internet_context: str, profile: UserProfile, db_history: dict = None) -> str:
    langchain_history = []
    if profile.summary:
        langchain_history.append(HumanMessage(content=f"Context of previous conversations: {profile.summary}"))
        langchain_history.append(AIMessage(content="Got it, I remember our previous talks."))
    for msg in db_history:
        if msg.username == "assistant":
            langchain_history.append(AIMessage(content=msg.text))
        else:
            langchain_history.append(HumanMessage(content=msg.text))

    return await get_llm_answer(
        text,
        history=langchain_history,
        bio_data=profile.bio_data,
        internet_context=internet_context
    )


async def get_internet_context(text: str, search_decision: dict = None) -> str:
    need_search = search_decision.get("need_search")
    query = search_decision.get("query")

    internet_context = "Web search was not initiated as it was unnecessary."
    if need_search and query:
        internet_context = "Web search was triggered, but no reliable results were found."
        raw_results = await duckduckgo_search(query)
        if raw_results:
            formatted_results = format_search_results(raw_results)
            summary_result = await get_web_search_summary(text, formatted_results)
            if summary_result:
                internet_context = summary_result
    return internet_context


async def summarize_old_messages(user_id: str, db_history: dict, profile: UserProfile) -> None:
    if db_history:
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

        await update_user_profile(int(user_id), summary=new_summary, bio_updates=new_bio)
        await mark_messages_as_summarized([m.id for m in to_process])

        logging.info("Archived %s messages for user %s", len(to_process), user_id)


async def request_answer_from_llm(user_id: int, text: str, user_name: str, db_history: dict, profile: UserProfile) -> str:
    ai_response = error_text
    if text is None:
        logging.warning("Skip invalid Kafka payload, text is null")
        return ai_response

    logging.info("Received request to LLM from %s: %s", user_id, text)
    request_msg = await save_message(user_id=user_id, text=text, username=user_name)
    request_msg_id = request_msg.id

    search_decision = await get_search_decision(text, db_history=db_history, bio_data=profile.bio_data)
    internet_context = await get_internet_context(text, search_decision)
    ai_response = await get_answer_from_llm(text, internet_context, profile, db_history)

    response_msg = await save_message(user_id=user_id, text=ai_response, username="assistant")
    response_msg_id = response_msg.id
    ai_response += f"\n\nCorrections: /{request_msg_id}{CORRECTION}\nTranslate: /{response_msg_id}{TRANSLATE}"
    logging.info("Received answer from LLM for %s: %s", user_id, ai_response)
    return ai_response
