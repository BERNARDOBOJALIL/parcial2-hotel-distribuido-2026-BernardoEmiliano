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

---

## Bonus que implementé (si aplica)

---

## Cosas que decidí NO hacer

(Ej: "no agregué tests porque preferí enfocarme en el flujo end-to-end", "no implementé saga porque no me dio tiempo", etc.)

---

## Si tuviera más tiempo, lo siguiente que mejoraría sería:
