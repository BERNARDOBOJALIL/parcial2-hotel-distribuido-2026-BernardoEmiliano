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

### b4 - overlap de fechas
**¿ Que hice?**
Reemplacé el filtro `Booking.check_in == check_in` por dos condiciones:`Booking.check_in < check_out` y `Booking.check_out > check_in`
**¿Por qué?**
solo detectaba conflicto si otra reserva empezaba exactamente el mismo día, puse mejor que el primero empiece antes de que el segundo termine, y que el primero termine después de que el segundo empiece para que si ambas condiciones se dan, la habitación no esté disponible
---

### B5 — race condition con with_for_update()
**¿Qué hice?**
Agregué `.with_for_update()` a la query que busca reservas dentro de `find_available_room`
**Por que?**
si dos requests llegan al mismo tiempo ambos consumers pueden leer "no hay conflictos". Con `.with_for_update()` queda en espera hasta que el primero hace commit, y es cuando ya ve la habitación ocupada y rechaza la reserva.
---

### B6 — Credenciales en env vars

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

---

## Bonus que implementé (si aplica)

---

## Cosas que decidí NO hacer

(Ej: "no agregué tests porque preferí enfocarme en el flujo end-to-end", "no implementé saga porque no me dio tiempo", etc.)

---

## Si tuviera más tiempo, lo siguiente que mejoraría sería:
