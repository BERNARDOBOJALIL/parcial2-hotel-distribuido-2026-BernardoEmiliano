# Declaración de uso de IA

> Llenen este archivo si alguno de los dos usó alguna herramienta de IA generativa (Claude, ChatGPT, Copilot, Gemini, etc.) durante el examen. Hacerlo es **obligatorio** y se evalúa con honestidad: declarar correctamente no penaliza, lo que penaliza es **no declarar** y que se detecte uso.
>
> Indiquen también **quién** de los dos integrantes la usó (puede ser uno solo, ambos, o ninguno).

## ¿Usaron IA?

- [x] Sí
- [ ] No

## ¿Quién la usó?

- [ ] Integrante 1 (Bernardo Bojalil)
- [ ] Integrante 2 (Emiliano Montoya)
- [x] Ambos

---

## Si la respuesta es "Sí":

### Herramientas usadas

- ChatGPT
- GitHub Copilot
- Claude

### Prompts principales

#### ChatGPT

1. **Prompt:** "cómo le cambio el nombre a una rama en Git?"
   **Para qué:** Consulta rápida de sintaxis para renombrar ramas locales y remotas sin romper el historial.
   **Quién lo usó:** Bernardo Bojalil
   **Qué tan útil fue:** 4/5

2. **Prompt:** "ahora tengo que cambiarle de nombre a unos commits, ¿se puede cambiar el nombre de commits pasados?"
   **Para qué:** Saber si era posible editar mensajes de commits ya pusheados usando interactive rebase.
   **Quién lo usó:** Bernardo Bojalil
   **Qué tan útil fue:** 3/5

3. **Prompt:** "Tengo este trabajo que tengo que resolver. Empezaremos por el Tier 1. Me dividí con mi compañero los bugs del Tier 1 dos y dos. ¿Cómo deberíamos hacer el GitHub? ¿Una rama por bug?" *(+ README de instrucciones adjunto)*
   **Para qué:** Definir la estrategia de ramas antes de empezar. La respuesta fue la estructura que terminamos usando: una rama por servicio (`booking-api`, `availability-core`, `payment-core`, `feature/Notifications`, `Tier3-Bonus`) para que cada quien viviera en la suya y los merges a `main` fueran limpios.
   **Quién lo usó:** Bernardo Bojalil
   **Qué tan útil fue:** 5/5

#### GitHub Copilot

1. **Prompt:** Explícame qué hace `with_for_update()`
   **Para qué:** Entender bien cómo funciona el bloqueo de filas en `availability-service`.
   **Quién lo usó:** Bernardo Bojalil
   **Qué tan útil fue:** 5/5

2. **Prompt:** Explícame paso a paso cómo funciona el `notification-service` completo.
   **Para qué:** Entender el flujo del consumer, los bindings y cómo debía quedar el log.
   **Quién lo usó:** Bernardo Bojalil
   **Qué tan útil fue:** 5/5

3. **Prompt:** Explícame cómo leer los logs para comprobar el flujo end-to-end.
   **Para qué:** Saber qué líneas buscar en `booking-api`, `availability-service`, `payment-service` y `notification-service`.
   **Quién lo usó:** Bernardo Bojalil
   **Qué tan útil fue:** 5/5

4. **Prompt:** "Corrí un loop de 15 reservas seguidas y en los logs veo que algunos pagos salen como FALLIDO y después aparece `marcada como CANCELLED` en availability-service.significa que la saga compensatoria está funcionando bien o debería ver algo más?"
   **Para qué:** Confirmar que el flujo de compensación estaba completo: payment publica `booking.cancelled` y availability lo recibe y actualiza el estado.
   **Quién lo usó:** Bernardo Bojalil
   **Qué tan útil fue:** 4/5

5. **Prompt:** "availability-service saca `Recibido booking.requested` pero después no aparece nada más, ni confirmación ni error. El estado en la base sigue en PENDING. que pasa?
   **Para qué:** Entender por qué el consumer recibía el evento pero el flujo se cortaba silenciosamente antes de actualizar la reserva.
   **Quién lo usó:** Bernardo Bojalil
   **Qué tan útil fue:** 5/5

6. **Prompt:** "En los logs de payment-service el mismo booking_id aparece dos veces: la primera  `Pago COMPLETADO`, la segunda  no loggea absolutamente nada. sí está detectando el duplicado o se está tragando el mensaje sin procesarlo?"
   **Para qué:** Verificar que `processed_events` estaba rechazando el redelivery correctamente y que no era un bug silencioso.
   **Quién lo usó:** Bernardo Bojalil
   **Qué tan útil fue:** 4/5


### Claude.ai

1. **Prompt:** "Ademas de cambiar mi auto_ack a false, que mas me ayudaría?" *(+ archivo main.py de availability-service adjunto)*
   **Para qué:** Identificar y corregir el bug B3 de `auto_ack=True` en RabbitMQ, cambiando a ack manual con `basic_ack` y `basic_nack(requeue=True)` para evitar pérdida de mensajes si el servicio crashea.
   **Quién lo usó:** Emiliano Montoya Velazquez
   **Qué tan útil fue:** 5/5

2. **Prompt:** "necesito hacer un pytest, explicame como funcionan*
   **Para qué:** Para yo poder generar los tests con pytest para la lógica de overlap 
   **Quién lo usó:** Emiliano Montoya Velazquez
   **Qué tan útil fue:** 3/5

3. **Prompt:** "qué hace `with_for_update()` en SQLAlchemy?"
   **Para qué:** Comprender cómo el `SELECT FOR UPDATE` bloquea filas dentro de una transacción para que dos consumers simultáneos no puedan confirmar la misma habitación al mismo tiempo.
   **Quién lo usó:** Emiliano Montoya Velazquez
   **Qué tan útil fue:** 4/5   

4. **Prompt:** "¿qué diferencia hay entre hacer dos queues separadas y una sola queue con dos bindings en RabbitMQ?"
    **Para qué:** Decidir la arquitectura del notification-service: entender que si el comportamiento ante `payment.completed` y `payment.failed` es el mismo, una sola queue con dos bindings es más simple y evita duplicar consumers innecesariamente.
    **Quién lo usó:** Emiliano Montoya Velazquez
    **Qué tan útil fue:** 5/5

5. **Prompt:** "¿cómo agrego healthchecks a servicios en docker-compose y qué comando uso para cada tipo de servicio?"
    **Para qué:** Entender la diferencia entre healthchecks de HTTP, de base de datos, de Redis y de RabbitMQ, y cómo configurar `interval` y `retries` para que los servicios dependientes esperen a que sus dependencias estén listas.
    **Quién lo usó:** Emiliano Montoya Velazquez
    **Qué tan útil fue:** 5/5

---

### ¿En qué partes los apoyó?

- Definición de la estrategia de ramas del repo para trabajar en paralelo sin conflictos.
- Dudas puntuales de sintaxis de Git.
- Entender `with_for_update()` y el bloqueo de filas para evitar race conditions.
- Seguir el flujo completo de `notification-service` y el sentido de los bindings.
- Interpretar logs para confirmar que todo estaba funcionando correctamente.
- Explicar como funciona un pytest.

### ¿Hubo cosas en las que la IA dio respuestas incorrectas o que tuvieron que corregir?

- En los prompts de interpretación de logs, las primeras respuestas asumían configuraciones que no teníamos (como múltiples consumers o retry policies), así que tuvimos que dar más contexto.
- Algunos ejemplos de código usaban nombres de variables que no coincidían con el repo y los ajustamos a mano.

### ¿Qué decidieron hacer manualmente sin IA y por qué?

- El código de todos los bugs se escribió a mano tomando como base los ejemplos vistos en clase, sin pedirle a la IA que generara ni completara código. La IA solo se usó para entender conceptos antes de implementarlos.
- La validación final con Docker y las capturas de evidencia las hicimos nosotros para confirmar que el sistema funcionaba de punta a punta.
- La lógica de la saga compensatoria y la tabla de idempotencia las implementamos nosotros; la IA solo nos ayudó a entender el patrón, no a escribir el código.
