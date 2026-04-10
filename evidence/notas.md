# Notas

## Qué hay en la carpeta

- Logs del flujo completo.
- Capturas de RabbitMQ.
- Curls que usé para probar.
- Salida de pruebas cuando apliqué.

## Cosas que me sirvieron

- Si un `POST /bookings` responde `REQUESTED`, eso no significa que ya quedó confirmada la reserva.
- La confirmación real se ve en `availability-service`.
- El pago puede salir `PAYMENT_COMPLETED` o `PAYMENT_FAILED` y ambos casos son válidos.
- Si falla el pago, `booking.cancelled` libera la reserva.

## Para revisar rápido

- `booking-api`: publica el evento inicial.
- `availability-service`: confirma o rechaza la reserva.
- `payment-service`: cobra o falla.
- `notification-service`: loggea la notificación final.
