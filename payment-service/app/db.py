"""Conexión async a Postgres para payment-service."""

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

# Arreglado bug: Configuración de la conexión a Postgres usando variables de entorno
_POSTGRES_USER = os.getenv("POSTGRES_USER", "hotel_user")
_POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "hotel_pass")
_POSTGRES_DB = os.getenv("POSTGRES_DB", "hotel_db")
_POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
_POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = (
    f"postgresql+asyncpg://{_POSTGRES_USER}:{_POSTGRES_PASSWORD}"
    f"@{_POSTGRES_HOST}:{_POSTGRES_PORT}/{_POSTGRES_DB}"
)


class Base(DeclarativeBase):
    pass


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)


engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
