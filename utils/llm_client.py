import json
import logging

from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_ollama import ChatOllama

from config import config
from .bio_update_prompt import bio_update_prompt
from .chat_prompt import (
    chat_prompt,
    summary_prompt,
    correction_prompt,
    translation_prompt,
    web_search_decision_prompt,
    web_search_summary_prompt,
)

llm = ChatOllama(
    base_url=config.ollama_url,
    model=config.ollama_model,
    timeout=180,
    temperature=0.6,
)

llm_json = ChatOllama(
    base_url=config.ollama_url,
    model=config.ollama_model,
    format="json",
    temperature=0.1,
)

chat_chain = chat_prompt | llm | StrOutputParser()
bio_chain = bio_update_prompt | llm_json | JsonOutputParser()
summary_chain = summary_prompt | llm | StrOutputParser()
correction_chain = correction_prompt | llm | StrOutputParser()
translation_chain = translation_prompt | llm | StrOutputParser()
web_search_decision_chain = web_search_decision_prompt | llm_json | JsonOutputParser()
web_search_summary_chain = web_search_summary_prompt | llm | StrOutputParser()


async def get_llm_answer(
        user_text: str,
        history: list = None,
        bio_data: dict = None,
        internet_context: str = None) -> str:

    if history is None:
        history = []
    if internet_context is None:
        internet_context = ""

    profile_str = "No specific info known yet."
    if bio_data:
        profile_str = "\n".join([f"- {k}: {v}" for k, v in bio_data.items()])

    try:
        response = await chat_chain.ainvoke({
            "user_input": user_text,
            "history": history,
            "user_profile": profile_str,
            "internet_context": internet_context
        })
        return response
    except Exception as e:
        return f"Sorry, my London tube is delayed (error: {e}) 🚇"


async def check_errors_with_llm(user_text: str, last_bot_message: str = None) -> str:
    try:
        if last_bot_message is None:
            last_bot_message = ""
        response = await correction_chain.ainvoke({
            "alex_response": last_bot_message,
            "user_input": user_text
        })

        cleaned_response = response.strip()
        if cleaned_response.lower().startswith("no mistakes") or not cleaned_response:
            return ""

        return cleaned_response
    except Exception as e:
        logging.error(f"Correction error: {e}")
        return ""


async def get_translation_with_llm(alex_text: str) -> str:
    try:
        response = await translation_chain.ainvoke({"alex_response": alex_text})
        return response.strip()
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return ""


async def update_bio_with_llm(current_bio: dict, new_messages_text: str) -> dict:
    try:
        return await bio_chain.ainvoke({
            "current_bio": json.dumps(current_bio, ensure_ascii=False),
            "new_messages": new_messages_text
        })
    except Exception as e:
        logging.error(f"Bio update error: {e}")
        return current_bio


async def update_summary_with_llm(current_summary: str, new_messages_text: str) -> str:
    try:
        return await summary_chain.ainvoke({
            "current_summary": current_summary or "No history yet.",
            "new_messages": new_messages_text
        })
    except Exception as e:
        logging.error(f"Summary update error: {e}")
        return current_summary


async def get_web_search_decision(user_text: str, history_text: str, profile_str: str) -> dict:
    try:
        search_decision = await web_search_decision_chain.ainvoke({
            "user_input": user_text,
            "history_text": history_text,
            "user_profile": profile_str,
        })

        need_search = bool(search_decision.get("need_search"))
        query = str(search_decision.get("query") or "").strip()
        reason = str(search_decision.get("reason") or "").strip()

        return {
            "need_search": need_search,
            "query": query
        }
    except Exception as e:
        logging.error(f"Get web search decision error: {e}")
        return {
            "need_search": False,
            "query": None
        }


async def get_web_search_summary(query: str, formatted_results: str) -> str:
    try:
        return await web_search_summary_chain.ainvoke({
                    "query": query,
                    "raw_results": formatted_results,
                })
    except Exception as e:
        logging.error(f"Get web search summary error: {e}")
        return ""
