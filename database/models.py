from sqlalchemy import BigInteger, String, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class MessageLog(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    username: Mapped[str | None] = mapped_column(String(32))
    text: Mapped[str] = mapped_column(String(4096))
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
