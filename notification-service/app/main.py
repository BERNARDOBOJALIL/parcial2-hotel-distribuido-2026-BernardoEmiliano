"""notification-service – consumer que loggea notificaciones de pago.

El servicio consume eventos `payment.completed` y `payment.failed` del
exchange `hotel`, y por cada uno loggea de forma estructurada el "envío" de
la notificación. No se manda email real: solo se loggea con un formato
específico que se evalúa.

Formato del log esperado:
[NOTIFICATION] booking_id=<id> event=PAYMENT_COMPLETED guest=<name> channel=email status=SENT
"""

import json
import logging
import os

import pika

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("notification-service")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")


# TODO 2: callback que parsea el JSON y loggea basic_ack si todo va bien, basic_nack con requeue=True si hay error
def callback(ch, method, properties, body):
    payload = json.loads(body)
    booking_id = payload.get("booking_id", "unknown")
    event = payload.get("event", "unknown")
    guest = payload.get("guest", "unknown")

    try:
        logger.info(
            "[NOTIFICATION] booking_id=%s event=%s guest=%s channel=email status=SENT",
            booking_id,
            event,
            guest,
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.error("Error procesando notificación %s: %s", booking_id, str(e))
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


def main() -> None:
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    # TODO 1: declarar el exchange 'hotel' y bindear la queue 'notifications'
    # Dos bindings sobre la misma queue para que reciba los dos
    channel.exchange_declare(exchange="hotel", exchange_type="topic")
    channel.queue_declare(queue="notifications", durable=False)
    channel.queue_bind(exchange="hotel", queue="notifications", routing_key="payment.completed")
    channel.queue_bind(exchange="hotel", queue="notifications", routing_key="payment.failed")

    # TODO 3: iniciar el consumer con ack manual (auto_ack=False) y arrancar
    channel.basic_consume(
        queue="notifications",
        on_message_callback=callback,
        auto_ack=False,
    )

    logger.info("notification-service esperando payment.completed / payment.failed...")
    channel.start_consuming()


if __name__ == "__main__":
    main()