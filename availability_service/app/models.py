"""Modelos ORM para Habitaciones y Reservas."""

from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    room_type: Mapped[str] = mapped_column(String(20), nullable=False)
    price_per_night: Mapped[int] = mapped_column(Integer, nullable=False)


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    booking_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    room_id: Mapped[int] = mapped_column(Integer, nullable=False)
    guest: Mapped[str] = mapped_column(String(100), nullable=False)
    check_in: Mapped[date] = mapped_column(Date, nullable=False)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="CONFIRMED")
