"""availability-service – consumer que valida disponibilidad y crea reservas."""

import json
import logging
import os
from datetime import date

import pika

from .db import SessionLocal, init_db
from .models import Booking, Room

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("availability-service")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")


def find_available_room(room_type: str, check_in: date, check_out: date) -> Room | None:
    """Busca una habitación del tipo solicitado libre en el rango dado.

    Devuelve la primera habitación disponible o None si ninguna lo está.
    """
    with SessionLocal() as session:
        candidates = session.query(Room).filter(Room.room_type == room_type).all()
        for room in candidates:
            # correccion 1:
            # había que poner dos rangos (check_in, check_out) para detectar cualquier solapamiento 
            # no solo comparar entre check in coo hacía antes para que cuando uno termine pueda iniciar el otro
            # correccion 2:
            # con with_for_update() bloqueamos las filas de reservas que podrían solaparse
            conflicts = (
                session.query(Booking)
                .filter(
                    Booking.room_id == room.id,
                    Booking.status == "CONFIRMED",
                    Booking.check_in < check_out,
                    Booking.check_out > check_in,
                )
                .with_for_update()  # bloquea las reservas que podrían duplicarse
                .all()
            )
            if not conflicts:
                return room
        return None


def process_booking(payload: dict) -> tuple[bool, str, int | None]:
    booking_id = payload["booking_id"]
    room_type = payload["room_type"]
    check_in = date.fromisoformat(payload["check_in"])
    check_out = date.fromisoformat(payload["check_out"])

    with SessionLocal() as session:
        room = find_available_room(room_type, check_in, check_out)
        if room is None:
            logger.info("Reserva %s rechazada: sin habitaciones %s", booking_id, room_type)
            return False, f"No hay habitaciones {room_type} disponibles", None

        booking = Booking(
            booking_id=booking_id,
            room_id=room.id,
            guest=payload["guest"],
            check_in=check_in,
            check_out=check_out,
            status="CONFIRMED",
        )
        session.add(booking)
        session.commit()
        logger.info("Reserva %s confirmada en habitación %s", booking_id, room.room_number)
        return True, "", room.id


def apply_cancellation_compensation(payload: dict) -> bool:
    booking_id = payload["booking_id"]
    with SessionLocal() as session:
        # La compensación solo aplica a reservas activas (CONFIRMED).
        # Si ya estaba cancelada/rechazada, no hay nada que liberar.
        booking = (
            session.query(Booking)
            .filter(
                Booking.booking_id == booking_id,
                Booking.status == "CONFIRMED",
            )
            .first()
        )
        if booking is None:
            # Registramos este caso para trazabilidad de saga.
            logger.warning("No se encontró reserva confirmada para cancelar: %s", booking_id)
            return False

        # Marcamos estado CANCELLED para liberar disponibilidad.
        booking.status = "CANCELLED"
        session.commit()
        # El commit garantiza persistencia antes de ackear el mensaje.
        logger.info("Reserva %s marcada como CANCELLED", booking_id)
        return True


def callback(ch, method, properties, body):
    payload = json.loads(body)
    routing_key = method.routing_key
    booking_id = payload["booking_id"]
    logger.info("Recibido %s: %s", routing_key, booking_id)

    try:
        if routing_key == "booking.requested":
            success, reason, room_id = process_booking(payload)
            if success:
                event = {**payload, "event": "BOOKING_CONFIRMED", "room_id": room_id}
                publish_key = "booking.confirmed"
            else:
                event = {**payload, "event": "BOOKING_REJECTED", "reason": reason}
                publish_key = "booking.rejected"

            ch.basic_publish(
                exchange="hotel",
                routing_key=publish_key,
                body=json.dumps(event).encode(),
                properties=pika.BasicProperties(content_type="application/json"),
            )
            logger.info("Publicado %s para %s", publish_key, booking_id)
        elif routing_key == "booking.cancelled":
            # Evento de compensación emitido por payment-service.
            apply_cancellation_compensation(payload)
        else:
            logger.warning("Routing key no soportado en availability-service: %s", routing_key)

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error("Error procesando %s: %s", booking_id, str(e))
        #correccion 3: requeue=True para que RabbitMQ reencole el mensaje
        # y no se pierda si el servicio crashea
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def main() -> None:
    init_db()
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange="hotel", exchange_type="topic")
    result = channel.queue_declare(queue="availability.requests", durable=False)
    channel.queue_bind(exchange="hotel", queue=result.method.queue, routing_key="booking.requested")
    # Se escucha también la compensación para liberar reservas tras payment.failed.
    channel.queue_bind(exchange="hotel", queue=result.method.queue, routing_key="booking.cancelled")

    # corrección 3: auto_ack=False para usar ack manual en el callback
    channel.basic_consume(
        queue=result.method.queue,
        on_message_callback=callback,
        auto_ack=False,
    )
    logger.info("availability-service esperando booking.requested / booking.cancelled...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
