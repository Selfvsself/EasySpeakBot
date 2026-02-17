from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from config import config

llm = ChatOllama(
    base_url=config.ollama_url,
    model=config.ollama_model,
    timeout=180,
    temperature=0.4,
)


async def get_llm_answer(user_text: str) -> str:
    messages = [
        SystemMessage(content="Ты — полезный ассистент в Телеграм-боте."),
        HumanMessage(content=user_text),
    ]
    response = await llm.ainvoke(messages)
    return response.content
