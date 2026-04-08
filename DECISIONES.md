# Decisiones técnicas

> Documenten brevemente las decisiones que tomaron resolviendo el examen. No copien del enunciado: expliquen con sus palabras qué hicieron y por qué. La intención es que al revisar pueda entender el razonamiento, no que repitan el problema.

---

## Bugs arreglados (Tier 1)

### B1 — Routing key
**Qué encontré:**

**Cómo lo arreglé:**

**Por qué esto era un problema:**

---

### B2 — Manejo de error en publish

---

### B3 — Ack manual

---

### B6 — Credenciales en env vars

**Qué encontré:** La conexión de `payment-service` a Postgres tenía usuario, password, host y base de datos escritos directamente en el código.

**Cómo lo arreglé:** Reemplacé la URL por una `DATABASE_URL` construida con `os.getenv(...)` usando `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y `POSTGRES_PORT`.

**Por qué esto era un problema:** Con los valores en el código no se puede cambiar configuración por ambiente y además se exponen credenciales y las podrían robar.

---

## notification-service completado

**Qué TODOs había:**

**Cómo los implementé:**

**Decisiones de diseño que tomé:**

---

## Bugs arreglados (Tier 2)

### B4 — Overlap de fechas

### B5 — Race condition con `with_for_update()`

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
