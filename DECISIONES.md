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
