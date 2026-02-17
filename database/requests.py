from sqlalchemy import select

from database.engine import async_session
from database.models import MessageLog


async def save_message(user_id: int, text: str, username: str = None):
    async with async_session() as session:
        new_msg = MessageLog(user_id=user_id, text=text, username=username)
        session.add(new_msg)
        await session.commit()


async def get_recent_messages(user_id: int, limit: int = 10):
    async with async_session() as session:
        query = (
            select(MessageLog)
            .filter(MessageLog.user_id == user_id)
            .order_by(MessageLog.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(query)
        messages = result.scalars().all()
        return messages[::-1]
