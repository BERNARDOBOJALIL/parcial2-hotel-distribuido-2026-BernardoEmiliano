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

**Cómo lo arreglé:** Envolví `await publish_booking(payload)` en `try/except`, registré el error en logs y devolví `HTTP 503 Service Unavailable`.

**Por qué esto era un problema:** El cliente podía interpretar que la reserva quedó aceptada cuando en realidad el evento ni siquiera se publicó. Con 503 comunicamos que algo falló.

**Comprobación:** Con RabbitMQ apagado (`docker compose stop rabbitmq`), al hacer `POST /bookings` el API respondió:

```json
{"detail":"Servicio de reservas no disponible. Intenta de nuevo más tarde :( )"}
```

---

### B3 — Ack manual

**Qué encontré:** El consumer de `availability-service` tenía `auto_ack=True`, lo que significa que RabbitMQ eliminaba el mensaje en el momento de entregarlo, antes de que se procesara.

**Cómo lo arreglé:** Cambié `auto_ack=True` a `auto_ack=False` en `basic_consume` y moví el acknowledgement al final del callback de forma manual.

**Por qué esto era un problema:** Si el servicio crasheaba después de recibir el mensaje pero antes de procesarlo, el mensaje se perdía para siempre. Con ack manual, el mensaje solo se elimina de la cola cuando se llama `basic_ack`, garantizando que se procesó correctamente.

---

### B6 — Credenciales en env vars

**Qué encontré:** La conexión de `payment-service` a Postgres tenía usuario, password, host y base de datos escritos directamente en el código.

**Cómo lo arreglé:** Reemplacé la URL por una `DATABASE_URL` construida con `os.getenv(...)` usando `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y `POSTGRES_PORT`.

**Por qué esto era un problema:** Con los valores en el código no se puede cambiar configuración por ambiente y además se exponen credenciales en el repositorio.

---

## notification-service completado

**Qué TODOs había:**
El skeleton tenía tres TODOs: declarar el exchange y bindear la queue a los routing keys de pago, implementar el callback que loggea la notificación con el formato requerido, e iniciar el consumer. Mientras no estuvieran resueltos, el servicio solo hacía un `sleep(60)` en loop y nunca consumía nada.

**Cómo los implementé:**
Para el TODO 1 declaré el exchange `hotel`, creé una queue llamada `notifications` y le hice dos bindings: uno para `payment.completed` y otro para `payment.failed`, de modo que una sola queue reciba los dos. Para el TODO 2 implementé el callback que parsea el JSON, extrae `booking_id`, `event` y `guest`, y loggea con el formato que dice ahí. Para el TODO 3 arranqué el consumer con `auto_ack=False` y `start_consuming()`, eliminando el loop falso del skeleton.

**Decisiones de diseño que tomé:**
Usé una sola queue con dos bindings en lugar de dos queues separadas, porque ambos eventos (`payment.completed` y `payment.failed`) se manejan exactamente igual: solo se loggea la notificación. No tiene sentido duplicar la lógica si es idéntica. También hice lo mismo que en `availability-service`: `basic_ack` cuando el log se escribe bien, `basic_nack(requeue=True)` si hay excepción, para no perder mensajes si el servicio falla a la mitad.

---

## Bugs arreglados (Tier 2)

### B4 — Overlap de fechas

**Qué encontré:** La query que verificaba disponibilidad solo detectaba conflicto si otra reserva empezaba exactamente el mismo día, ignorando todos los demás casos de solapamiento.

**Cómo lo arreglé:** Reemplacé el filtro `Booking.check_in == check_in` por dos condiciones: `Booking.check_in < check_out` y `Booking.check_out > check_in`.

**Por qué esto era un problema:** Con el filtro original, una reserva del 5 al 10 no bloqueaba una nueva reserva del 7 al 12 porque el check_in no era exactamente igual. Con las dos condiciones nuevas, cualquier solapamiento parcial o total queda correctamente detectado.

---

### B5 — Race condition con `with_for_update()`

**Qué encontré:** Si dos requests llegaban al mismo tiempo, ambos consumers podían leer "no hay conflictos" antes de que cualquiera hiciera commit, y ambos confirmaban la misma habitación.

**Cómo lo arreglé:** Agregué `.with_for_update()` a la query que busca reservas dentro de `find_available_room`.

**Por qué esto era un problema:** Sin el bloqueo, la validación de disponibilidad no era atómica. Con `.with_for_update()`, el segundo request queda en espera hasta que el primero hace commit, y en ese momento ya ve la habitación ocupada y rechaza la reserva correctamente.

---

### B7 — Idempotencia

**Qué encontré:** Si RabbitMQ reentregaba el mismo `booking.confirmed`, el `payment-service` podía volver a cobrar porque no existía control de eventos ya procesados.

**Cómo lo arreglé:** Agregué una tabla `processed_events` con `event_id` como llave primaria. Antes de cobrar, el servicio intenta registrar el `event_id`; si ya existe, detecta duplicado, lo loggea y no hace el cobro.

**Por qué esto era un problema:** Sin idempotencia, un redelivery puede generar doble cobro.

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

### Saga compensatoria

**Qué quité y qué puse:**
- **En `payment-service`** antes solo se publicaba `payment.completed` o `payment.failed`; **agregué** la publicación de `booking.cancelled` cuando el pago falla.
- **En `availability-service`** antes la cola solo escuchaba `booking.requested`; **agregué** un segundo binding a `booking.cancelled` y una función de compensación que cambia el estado de la reserva de `CONFIRMED` a `CANCELLED`.
- En el callback de availability **separé el flujo por `routing_key`** para no mezclar la lógica de confirmación normal con la lógica de compensación.

**Por qué lo hice así:** El fallo de pago no debe dejar inventario bloqueado. Con este evento de compensación desacoplado, cada servicio mantiene su responsabilidad y el estado final queda consistente.

**Comprobación (logs):**

```text
❯ for i in $(seq 1 15); do
	d=$(printf "%02d" $i)
	d2=$(printf "%02d" $((i+1)))
	curl -s -X POST http://localhost:8000/bookings \
		-H "Content-Type: application/json" \
		-d "{\"guest\":\"Saga Test $i\",\"room_type\":\"single\",\"check_in\":\"2026-11-$d\",\"check_out\":\"2026-11-$d2\"}" >/dev/null
done
❯ docker compose logs --tail=400 payment-service availability-service | \
pipe> 
pipe> grep -E "Pago FALLIDO|Publicado payment.failed|Publicado booking.cancelled|marcada como CANCELLED"
availability-service-1  | 2026-04-09 21:58:37,943 availability-service INFO Reserva 6718f291-76f5-44d1-a8b6-6faa6089fd0a marcada como CANCELLED
availability-service-1  | 2026-04-09 21:58:38,202 availability-service INFO Reserva 6b9b1c09-f6d5-4014-bdb9-2900fbe7afd3 marcada como CANCELLED
payment-service-1       | 2026-04-09 21:58:37,876 payment-service WARNING Pago FALLIDO booking=6718f291-76f5-44d1-a8b6-6faa6089fd0a motivo=Tarjeta rechazada por el banco simulado
payment-service-1       | 2026-04-09 21:58:37,923 payment-service INFO Publicado payment.failed para 6718f291-76f5-44d1-a8b6-6faa6089fd0a
payment-service-1       | 2026-04-09 21:58:37,926 payment-service INFO Publicado booking.cancelled para 6718f291-76f5-44d1-a8b6-6faa6089fd0a
payment-service-1       | 2026-04-09 21:58:38,145 payment-service WARNING Pago FALLIDO booking=6b9b1c09-f6d5-4014-bdb9-2900fbe7afd3 motivo=Tarjeta rechazada por el banco simulado
payment-service-1       | 2026-04-09 21:58:38,171 payment-service INFO Publicado payment.failed para 6b9b1c09-f6d5-4014-bdb9-2900fbe7afd3
payment-service-1       | 2026-04-09 21:58:38,176 payment-service INFO Publicado booking.cancelled para 6b9b1c09-f6d5-4014-bdb9-2900fbe7afd3
```

---

### Tests

**Qué probé:** La lógica de overlap de fechas con 6 casos distintos, y la función de compensación `apply_cancellation_compensation` con 2 casos.

**Casos de overlap probados:**
- Reservas consecutivas (back-to-back) — no deben solaparse
- Solapamiento parcial por el inicio
- Solapamiento parcial por el fin
- Rango completamente contenido dentro de otro
- Mismo rango exacto
- Rango completamente anterior — no deben solaparse

**Casos de compensación probados:**
- Reserva confirmada encontrada — debe marcarse como `CANCELLED` y retornar `True`
- Reserva no encontrada — debe retornar `False` sin romper

**Por qué esas funciones:** Son las dos funciones puras más críticas del sistema. El overlap es el corazón de la validación de disponibilidad, y la compensación es la pieza que garantiza consistencia cuando un pago falla. Si alguna de las dos falla silenciosamente, el sistema queda en un estado corrupto sin ningún error visible.

**Cómo correr los tests:**

```bash
cd availability-service
pip install pytest
pytest tests/ -v
```

**Resultado obtenido:**

```text
================================================= test session starts =================================================
platform win32 -- Python 3.13.1, pytest-9.0.2, pluggy-1.6.0
collected 8 items

tests/test_availability.py::TestOverlapLogic::test_sin_solapamiento_consecutivo PASSED        [ 12%]
tests/test_availability.py::TestOverlapLogic::test_solapamiento_parcial_inicio PASSED         [ 25%]
tests/test_availability.py::TestOverlapLogic::test_solapamiento_parcial_fin PASSED            [ 37%]
tests/test_availability.py::TestOverlapLogic::test_solapamiento_contenido PASSED              [ 50%]
tests/test_availability.py::TestOverlapLogic::test_mismo_rango_exacto PASSED                  [ 62%]
tests/test_availability.py::TestOverlapLogic::test_sin_solapamiento_antes PASSED              [ 75%]
tests/test_availability.py::TestCancellationCompensation::test_cancela_reserva_confirmada PASSED [ 87%]
tests/test_availability.py::TestCancellationCompensation::test_no_encuentra_reserva PASSED    [100%]
```

---

## Cosas que decidí NO hacer

Hicimos todo lo que pedía el examen. Los tests podrían ser más extensos y cubrir más casos edge, pero nos limitó el tiempo.

---

## Si tuviera más tiempo, lo siguiente que mejoraría sería:

- Un front que permita visualizar mejor las funciones
- Hacer los datos de las colas durables para producción
  
