from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama

from config import config
from .prompts import chat_prompt

llm = ChatOllama(
    base_url=config.ollama_url,
    model=config.ollama_model,
    timeout=180,
    temperature=0.6,
)

chain = chat_prompt | llm | StrOutputParser()


async def get_llm_answer(user_text: str, history: list = None) -> str:
    if history is None:
        history = []

    try:
        response = await chain.ainvoke({
            "user_input": user_text,
            "history": history
        })
        return response
    except Exception as e:
        return f"Sorry, my London tube is delayed (error: {e}) 🚇"
