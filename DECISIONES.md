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

---

### B3 — Ack manual

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
