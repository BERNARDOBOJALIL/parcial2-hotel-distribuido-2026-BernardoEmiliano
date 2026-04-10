"""Engine y fábrica de sesiones SQLAlchemy + seed de habitaciones."""

import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base, Room

logger = logging.getLogger("availability-service.db")

_POSTGRES_USER = os.getenv("POSTGRES_USER", "hotel_user")
_POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "hotel_pass")
_POSTGRES_DB = os.getenv("POSTGRES_DB", "hotel_db")
_POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
_POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = (
    f"postgresql+psycopg2://{_POSTGRES_USER}:{_POSTGRES_PASSWORD}"
    f"@{_POSTGRES_HOST}:{_POSTGRES_PORT}/{_POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

SEED_ROOMS = [
    {"room_number": "101", "room_type": "single", "price_per_night": 800},
    {"room_number": "102", "room_type": "single", "price_per_night": 850},
    {"room_number": "201", "room_type": "double", "price_per_night": 1500},
    {"room_number": "202", "room_type": "double", "price_per_night": 1500},
    {"room_number": "301", "room_type": "suite",  "price_per_night": 3200},
]


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        if session.query(Room).count() == 0:
            for r in SEED_ROOMS:
                session.add(Room(**r))
            session.commit()
            logger.info("Habitaciones iniciales insertadas: %d", len(SEED_ROOMS))
        else:
            logger.info("Tabla rooms ya tiene datos – omitiendo seed")
