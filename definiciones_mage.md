# Definiciones del Proyecto y Pipelines

## Proyecto de Mage: `quickbooks_backfill`

- **Objetivo:** extraer datos de QuickBooks (`invoices`, `customers`, `items`) y cargarlos en el esquema `raw` en Postgres.
- **Componentes:**
  - **Loaders:** llamados a la API de QuickBooks con autenticación OAuth2 (`client_id`, `client_secret`, `refresh_token`).
  - **Transformers:** enriquecen los registros agregando metadatos (`extract_window_start_utc`, `extract_window_end_utc`, `page_number`, `page_size`, `request_payload`).
  - **Exporters:** insertan en Postgres (`raw.qb_<entidad>`) con **UPSERT** lo que asegura idempotencia.

---

## Pipelines

### `qb_invoices_backfill`
- **Parámetros:**
  - `extract_window_start_utc`
  - `extract_window_end_utc`
  - `page_size`
  - `page_number`
- **Segmentación:** uso de `start_position` y `max_results` de la API de QuickBooks.
- **Reintentos:** 3 intentos con backoff exponencial.
- **Runbook:**
  1. Validar secretos cargados en Mage (`qb_client_id`, `qb_client_secret`, `qb_refresh`, `pg_host`, `pg_port`, `pg_db`, `pg_user`, `pg_password`).
  2. Lanzar trigger one-time.
  3. Verificar inserción en Postgres (`SELECT COUNT(*) FROM raw.qb_invoices;`).

---

### `qb_customers_backfill`
- **Parámetros:** iguales que invoices.
- **Segmentación:** paginación API de QuickBooks.
- **Reintentos:** hasta 3 intentos.
- **Runbook:** verificar inserción en `raw.qb_customers`.

---

### `qb_items_backfill`
- **Parámetros:** iguales que invoices.
- **Segmentación:** paginación API.
- **Reintentos:** hasta 3 intentos.
- **Runbook:** verificar inserción en `raw.qb_items`.

---

## Trigger One-Time

- **Nombre:** Hay uno para cada uno con Trigger_<entidad>
- **Tipo:** One-time
- **Fecha/hora UTC:** 2026-01-27 04:48 UTC
- **Equivalencia Guayaquil:** 2026-01-26 23:48 GYE
- **Política:** deshabilitar el trigger después de ejecutarse para evitar corridas accidentales.
