"""booking-api – punto de entrada HTTP para reservas de hotel."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from .config import settings  # noqa: F401
from .rabbitmq import publish_booking
from .redis_client import get_redis
from .schemas import BookingCreated, BookingIn, BookingStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("booking-api")

app = FastAPI(title="HotelBook – Booking API")


@app.post("/bookings", response_model=BookingCreated, status_code=202)
async def create_booking(body: BookingIn):
    """Crea una solicitud de reserva y la publica al broker."""
    if body.check_out <= body.check_in:
        raise HTTPException(
            status_code=400, detail="check_out debe ser posterior a check_in"
        )

    booking_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    logger.info("Nueva reserva %s para %s", booking_id, body.guest)

    r = get_redis()
    await r.hset(
        f"booking:{booking_id}",
        mapping={"status": "REQUESTED", "last_update": now},
    )

    payload = {
        "booking_id": booking_id,
        "guest": body.guest,
        "room_type": body.room_type,
        "check_in": body.check_in.isoformat(),
        "check_out": body.check_out.isoformat(),
    }

    # Bug arreglado al encapsular publish en try/except/finally para devolver 503 y asegurar queya se cerró Redis
    try:
        await publish_booking(payload)
    except Exception:
        logger.exception("Error publicando booking.requested para booking_id=%s", booking_id)
        raise HTTPException(
            status_code=503,
            detail="Servicio de reservas no disponible. Intenta de nuevo más tarde :( )",
        )
    finally:
        await r.aclose()

    return BookingCreated(booking_id=booking_id, status="REQUESTED")


@app.get("/bookings/{booking_id}", response_model=BookingStatus)
async def get_booking(booking_id: str):
    r = get_redis()
    data = await r.hgetall(f"booking:{booking_id}")
    await r.aclose()

    if not data:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    return BookingStatus(
        booking_id=booking_id,
        status=data.get("status", "UNKNOWN"),
        last_update=data.get("last_update", ""),
        reason=data.get("reason"),
    )


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
