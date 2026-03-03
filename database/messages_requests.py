from sqlalchemy import select, update

from database.engine import async_session
from database.models import ChatMessage


async def save_message(user_id: int, text: str, username: str = None) -> ChatMessage:
    async with async_session() as session:
        new_msg = ChatMessage(user_id=user_id, text=text, username=username)
        session.add(new_msg)
        await session.commit()
        await session.refresh(new_msg)
        return new_msg


async def get_message_by_id(msg_id: int) -> ChatMessage | None:
    async with async_session() as session:
        return await session.get(ChatMessage, msg_id)


async def get_unsummarized_messages(user_id: int):
    async with async_session() as session:
        query = (
            select(ChatMessage)
            .filter(ChatMessage.user_id == user_id, ChatMessage.is_summarized == False)
            .order_by(ChatMessage.created_at.asc())
        )
        result = await session.execute(query)
        return result.scalars().all()


async def mark_messages_as_summarized(message_ids: list[int]):
    async with async_session() as session:
        query = (
            update(ChatMessage)
            .where(ChatMessage.id.in_(message_ids))
            .values(is_summarized=True)
        )
        await session.execute(query)
        await session.commit()
