from database.engine import async_session
from database.models import MessageLog


async def log_message(user_id: int, text: str, username: str = None):
    async with async_session() as session:
        new_msg = MessageLog(user_id=user_id, text=text, username=username)
        session.add(new_msg)
        await session.commit()
