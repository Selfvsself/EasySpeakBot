from sqlalchemy import BigInteger, String, DateTime, func, Boolean, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ChatMessage(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    username: Mapped[str | None] = mapped_column(String(32))
    text: Mapped[str] = mapped_column(String(4096))
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    is_summarized: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class UserProfile(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    bio_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
