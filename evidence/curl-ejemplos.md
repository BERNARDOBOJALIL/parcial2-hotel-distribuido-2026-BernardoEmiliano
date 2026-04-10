# Curl ejemplos

## 1) Solicitud principal (la que usamos en evidencia)

```bash
curl -s -X POST http://localhost:8000/bookings \
  -H "Content-Type: application/json" \
  -d '{"guest":"Evidencia","room_type":"double","check_in":"2026-12-01","check_out":"2026-12-03"}'
```

Respuesta:

```json
{"booking_id":"c916cd14-59d0-4d53-b0bc-ebdda65808db","status":"REQUESTED"}
```

## 2) Otra reserva (single)

```bash
curl -s -X POST http://localhost:8000/bookings \
  -H "Content-Type: application/json" \
  -d '{"guest":"Evidencia 2","room_type":"single","check_in":"2026-12-05","check_out":"2026-12-07"}'
```

Respuesta:

```json
{"booking_id":"101ec932-6204-4e00-93de-78889800be66","status":"REQUESTED"}
```


## 3) Otra reserva valida (suite)

```bash
curl -s -X POST http://localhost:8000/bookings \
  -H "Content-Type: application/json" \
  -d '{"guest":"Evidencia 3","room_type":"suite","check_in":"2026-12-10","check_out":"2026-12-12"}'
```

Respuesta:

```json
{"booking_id":"68568efa-ae6a-4f57-b114-9a6029c5db56","status":"REQUESTED"}
```



## 4) Caso invalido: fechas invertidas (debe regresar 400)

```bash
curl -i -X POST http://localhost:8000/bookings \
  -H "Content-Type: application/json" \
  -d '{"guest":"Error Fechas","room_type":"double","check_in":"2026-12-20","check_out":"2026-12-19"}'
```

Respuesta:

```json
HTTP/1.1 400 Bad Request
date: Fri, 10 Apr 2026 02:00:06 GMT
server: uvicorn
content-length: 52
content-type: application/json

{"detail":"check_out debe ser posterior a check_in"}
```

## 5) Prueba de concurrencia B5

```bash
(
  curl -s -X POST http://localhost:8000/bookings \
    -H "Content-Type: application/json" \
    -d '{"guest":"Race A","room_type":"suite","check_in":"2026-12-20","check_out":"2026-12-22"}' &

  curl -s -X POST http://localhost:8000/bookings \
    -H "Content-Type: application/json" \
    -d '{"guest":"Race B","room_type":"suite","check_in":"2026-12-20","check_out":"2026-12-22"}' &

  wait
)
```
Respuesta:

```json
{"booking_id":"09663fb3-42c8-4bc8-8ea3-bafccb2fca7f","status":"REQUESTED"}{"booking_id":"766dba29-fb8f-40c3-8e4d-fd423ef68549","status":"REQUESTED"}%   
```

