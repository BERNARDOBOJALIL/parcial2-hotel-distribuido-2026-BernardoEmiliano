# Decisiones técnicas

> Documenten brevemente las decisiones que tomaron resolviendo el examen. No copien del enunciado: expliquen con sus palabras qué hicieron y por qué. La intención es que al revisar pueda entender el razonamiento, no que repitan el problema.

---

## Bugs arreglados (Tier 1)

### B1 — Routing key
**Qué encontré:** El publisher de `booking-api` enviaba el evento con un routing key distinto al que consumía `availability-service`, así que el mensaje llegaba al exchange pero no había ninguna cola que esperara esos mensajes.

**Cómo lo arreglé:** Cambié el routing key de publicación a `booking.requested`, que es el mismo valor que usa el consumer.



**Por qué esto era un problema:** En un exchange de tipo `topic`, si no coincide con el binding, el mensaje queda sin destinatario.

**Comprobación:** Al correr `docker compose logs availability-service | grep "Recibido"` apareció esta línea, confirmando que el consumer sí recibió el evento:

```text
availability-service-1  | 2026-04-08 16:02:49,489 availability-service INFO Recibido booking.requested: a19ea6eb-e3f8-445e-ac06-475684ae0660
```

---

### B2 — Manejo de error en publish

**Qué encontré:** El endpoint de creación de reservas no manejaba el error del publish a RabbitMQ. Si el broker fallaba, no se devolvía algo que dijera que no estaba disponible.

**Cómo lo arreglé:** Envolví `await publish_booking(payload)` en `try/except`, registré el error en logs y devolví `HTTP 503 Service Unavailable`

**Por qué esto era un problema:** El cliente podía interpretar que la reserva quedó aceptada cuando en realidad el evento ni siquiera se publicó. Con 503 comunicamos que algo falló.

**Comprobación:** Con RabbitMQ apagado (`docker compose stop rabbitmq`), al hacer `POST /bookings` el API respondió:

```json
{"detail":"Servicio de reservas no disponible. Intenta de nuevo más tarde :( )"}
```

---

### B3 — Ack manual

**¿Qué hice?**
Cambié `auto_ack=True` a `auto_ack=false` en `basic_consume`, y moví el acknowledgement al final del callback de forma manual
**¿Por qué?**
Con `auto_ack=True` RabbitMQ elimina el mensaje de la cola en el momento en que lo entrega al consumer, Si crashea, el mensaje se pierde. Con ack manual, el mensaje solo se elimina cuando yo llamo `basic_ack`

---

### B6 — Credenciales en env vars

**Qué encontré:** La conexión de `payment-service` a Postgres tenía usuario, password, host y base de datos escritos directamente en el código.

**Cómo lo arreglé:** Reemplacé la URL por una `DATABASE_URL` construida con `os.getenv(...)` usando `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y `POSTGRES_PORT`.

**Por qué esto era un problema:** Con los valores en el código no se puede cambiar configuración por ambiente y además se exponen credenciales y las podrían robar.

---

## notification-service completado

**Qué TODOs había:**
El skeleton tenía tres TODOs: declarar el exchange y bindear la queue a los routing keys de pago, implementar el callback que loggea la notificación con el formato requerido, e iniciar el consumer. Mientras no estuvieran resueltos, el servicio solo hacía un `sleep(60)` en loop y nunca consumía nada.

**Cómo los implementé:**
Para el TODO 1 declaré el exchange `hotel`, creé una queue llamada `notifications` y le hice dos bindings: uno para `payment.completed` y otro para `payment.failed`, de modo que una sola queue reciba los dos. Para el TODO 2 implementé el callback que parsea el JSON, extrae `booking_id`, `event` y `guest`, y loggea con el formato que dice ahí. Para el TODO 3 arranqué el consumer con `auto_ack=False` y `start_consuming()`, eliminando el loop falso del skeleton.

**Decisiones de diseño que tomé:**
Usé una sola queue con dos bindings en lugar de dos queues separadas, porque ambos eventos (`payment.completed` y `payment.failed`) se manejan exactamente igual: solo se loggea la notificación. No tiene sentido hacerlo dos veces si la logica es igual. También hice lo mismo que en availability-service: `basic_ack` cuando el log se escribe bien, `basic_nack(requeue=True)` si hay excepción, para no perder mensajes si el servicio falla a la mitad.

---

## Bugs arreglados (Tier 2)

### b4 - overlap de fechas
**¿ Que hice?** Reemplacé el filtro `Booking.check_in == check_in` por dos condiciones:`Booking.check_in < check_out` y `Booking.check_out > check_in`
**¿Por qué?** solo detectaba conflicto si otra reserva empezaba exactamente el mismo día, puse mejor que el primero empiece antes de que el segundo termine, y que el primero termine después de que el segundo empiece para que si ambas condiciones se dan, la habitación no esté disponible

---

### B5 — race condition con with_for_update()

**¿Qué hice?** Agregué `.with_for_update()` a la query que busca reservas dentro de `find_available_room`
**Por que?** si dos requests llegan al mismo tiempo ambos consumers pueden leer "no hay conflictos". Con `.with_for_update()` queda en espera hasta que el primero hace commit, y es cuando ya ve la habitación ocupada y rechaza la reserva.

---

### B7 — Idempotencia

**Qué encontré:** Si RabbitMQ reentregaba el mismo `booking.confirmed`, el `payment-service` podía volver a cobrar porque no existía control de eventos ya procesados.

**Cómo lo arreglé:** Agregué una tabla `processed_events` con `event_id` como llave primaria. Antes de cobrar, el servicio intenta registrar el `event_id`; si ya existe, detecta duplicado, lo loggea y no hace el cobro.

**Por qué esto era un problema:** Sin idempotencia, un redelivery puede generar doble cobro

**Comprobación:**

```text
❯ docker compose logs payment-service --tail=200
payment-service-1  | 2026-04-08 17:14:15,861 payment-service INFO payment-service esperando booking.confirmed...
payment-service-1  | 2026-04-08 17:16:35,804 payment-service INFO Recibido booking.confirmed: b7-booking-001
payment-service-1  | 2026-04-08 17:16:36,163 payment-service INFO Pago COMPLETADO booking=b7-booking-001 monto=1500
payment-service-1  | 2026-04-08 17:16:36,180 payment-service INFO Publicado payment.completed para b7-booking-001
payment-service-1  | 2026-04-08 17:16:47,395 payment-service INFO Recibido booking.confirmed: b7-booking-001
payment-service-1  | 2026-04-08 17:16:47,405 payment-service INFO Evento duplicado ignorado: event_id=evt-b7-001 booking_id=b7-booking-001
❯ docker compose exec postgres psql -U hotel_user -d hotel_db -c \
"SELECT booking_id, COUNT(*) FROM payments WHERE booking_id='b7-booking-001' GROUP BY booking_id;"
	 booking_id   | count 
----------------+-------
 b7-booking-001 |     1
(1 row)

❯ docker compose exec postgres psql -U hotel_user -d hotel_db -c \
"SELECT event_id, COUNT(*) FROM processed_events WHERE event_id='evt-b7-001' GROUP BY event_id;"
	event_id  | count 
------------+-------
 evt-b7-001 |     1
(1 row)
```

---

## Bonus que implementé (si aplica)

---

## Cosas que decidí NO hacer

(Ej: "no agregué tests porque preferí enfocarme en el flujo end-to-end", "no implementé saga porque no me dio tiempo", etc.)

---

## Si tuviera más tiempo, lo siguiente que mejoraría sería:
