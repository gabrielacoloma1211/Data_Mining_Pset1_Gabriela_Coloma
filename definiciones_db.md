# Definiciones de Base de Datos: Esquema `raw`

Todas las tablas se almacenan en el esquema `raw`.  
Incluyen **metadatos** para trazabilidad y asegurar **idempotencia** (UPSERT sobre `id`).

---

## Tabla: `raw.qb_invoices`

- **id:** `TEXT` → PK, identificador único de la factura en QuickBooks.
- **payload:** `JSONB NOT NULL` → registro completo de la API.
- **ingested_at_utc:** `TIMESTAMPTZ NOT NULL` → timestamp de ingesta.
- **extract_window_start_utc:** `TIMESTAMPTZ` → inicio de ventana de extracción.
- **extract_window_end_utc:** `TIMESTAMPTZ` → fin de ventana de extracción.
- **page_number:** `INT` → número de página.
- **page_size:** `INT` → tamaño de página.
- **request_payload:** `JSONB` → parámetros de request.


---

## Tabla: `raw.qb_customers`

- **id:** `TEXT` → PK, identificador único de cliente en QuickBooks.
- **payload:** `JSONB NOT NULL`
- **ingested_at_utc:** `TIMESTAMPTZ NOT NULL`
- **extract_window_start_utc:** `TIMESTAMPTZ`
- **extract_window_end_utc:** `TIMESTAMPTZ`
- **page_number:** `INT`
- **page_size:** `INT`
- **request_payload:** `JSONB`


---

## Tabla: `raw.qb_items`

- **id:** `TEXT` → PK, identificador único de ítem en QuickBooks.
- **payload:** `JSONB NOT NULL`
- **ingested_at_utc:** `TIMESTAMPTZ NOT NULL`
- **extract_window_start_utc:** `TIMESTAMPTZ`
- **extract_window_end_utc:** `TIMESTAMPTZ`
- **page_number:** `INT`
- **page_size:** `INT`
- **request_payload:** `JSONB`

