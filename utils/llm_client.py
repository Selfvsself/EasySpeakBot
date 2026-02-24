import json
import logging

from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_ollama import ChatOllama

from config import config
from .bio_update_prompt import bio_update_prompt
from .chat_prompt import chat_prompt, summary_prompt

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

# Цепочки
chat_chain = chat_prompt | llm | StrOutputParser()
bio_chain = bio_update_prompt | llm_json | JsonOutputParser()
summary_chain = summary_prompt | llm | StrOutputParser()


async def get_llm_answer(user_text: str, history: list = None, bio_data: dict = None) -> str:
    if history is None:
        history = []

    profile_str = "No specific info known yet."
    if bio_data:
        profile_str = "\n".join([f"- {k}: {v}" for k, v in bio_data.items()])

    try:
        response = await chat_chain.ainvoke({
            "user_input": user_text,
            "history": history,
            "user_profile": profile_str  # Передаем сюда
        })
        return response
    except Exception as e:
        return f"Sorry, my London tube is delayed (error: {e}) 🚇"


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
