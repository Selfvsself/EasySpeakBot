from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import config
from database.models import Base

engine = create_async_engine(url=config.db_url, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


# Функция для создания таблиц (если не используешь alembic на старте)
async def proceed_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
