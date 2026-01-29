# Data_Mining_Pset1_Gabriela_Coloma

Problem Set 1 - Data Mining

Nombre: Gabriela Coloma  
Código: 00325312  

***Resumen***  
El proyecto construye tres pipelines de backfill histórico desde QuickBooks Online (QBO) para las entidades: Invoices, Customers e Items.  
Los datos extraídos se guardan en Postgres (esquema raw).  
Los pipelines se orquestaron en Mage, se despliegan con Docker Compose y se gestionaron las credenciales con Mage Secrets.  

---

***Diagrama de arquitectura***

<img width="740" height="150" alt="Screenshot 2026-01-29 at 4 01 03 PM" src="https://github.com/user-attachments/assets/814cf5f8-ca91-4984-9629-d671d68f3a47" />



---

***Pasos para levantar contenedores y configurar proyecto***  

1. Clonar este repositorio:  
git clone <repo_url>
cd <repo>


2. Levantar servicios:  
docker compose up -d
 

3. Apagar servicios:  
docker compose down


Servicios:  
- warehouse: PostgreSQL (5432)  
- warehouseui: pgAdmin (8081)  
- scheduler: Mage (6789) 

---

***Gestión de secretos***  
Todos los secretos se configuraron en Mage Secrets, no están en el código ni en el repo.  
Se llaman desde el código con la función `get_secret_value()`.  

| Nombre secreto     | Para qué sirve                        | Cada cuánto se cambia       | Responsable |
|--------------------|---------------------------------------|-----------------------------|-------------|
| `qb_client_id`     | Identificador de la app en QBO        | Solo si cambia la app       | Yo |
| `qb_client_secret` | Llave secreta de la app QBO           | Cada 180 días o si hay fuga | Yo |
| `qb_refresh`       | Token para pedir nuevos accesos a QBO | Cada 101 días (por QBO)     | Yo |
| `qb_realm`         | ID de la empresa en QBO               | Nunca cambia                | Yo |
| `pg_host`          | Dirección del servidor Postgres       | Solo si cambia infra        | Yo |
| `pg_port`          | Puerto de conexión a Postgres         | Nunca                    | Yo |
| `pg_db`            | Nombre de la base de datos            | Solo si se crea otra        | Yo |
| `pg_user`          | Usuario para entrar a Postgres        | Solo si se compromete       | Yo |
| `pg_password`      | Contraseña de Postgres                | Cada 90 días o si hay fuga  | Yo |

---

***Pipelines***  
Existen 3 pipelines: uno para Invoices, otro para Customers y otro para Items.  

Parámetros:  
- fecha_inicio (UTC)  
- fecha_fin (UTC)  
- page_size (default: 100)  

Segmentación:  
- Se divide en chunks de 7 días  
- Paginación con startposition y maxresults 

Límites y reintentos:  
- Manejo del error 429 (Too Many Requests) con backoff exponencial  
- Hasta 5 reintentos con backoff inicial de 2 segundos  

Runbook:  
- Ejecutar pipeline con rango deseado  
- Si falla:  
- Revisar logs en Mage  
- Reintentar ejecución (idempotente, no duplica registros)  
- Si el fallo es por auth, refrescar tokens en Mage Secrets  

---

***Trigger one-time***  
Configurados para las tres entidades:  
- trigger_invoice  
- trigger_customers  
- trigger_items  

Frecuencia: @once  
Ejecución registrada: 2026-01-27 04:48 (UTC)


Equivalencia Guayaquil: UTC −5 → 23:48 hora local (2026-01-26) ≈ 04:48 UTC
Política: deshabilitados automáticamente tras ejecución (completed).  

---

***Esquema RAW***  
Tablas en el esquema `raw`:  
- raw.qb_invoices  
- raw.qb_customers  
- raw.qb_items  

Columnas:  
- id (TEXT, PK) → Identificador único del registro  
- payload (JSONB, NOT NULL) → Objeto JSON completo desde QBO  
- ingested_at_utc (TIMESTAMPTZ, NOT NULL) → Momento de inserción (UTC)  
- extract_window_start_utc (TIMESTAMPTZ, NOT NULL) → Inicio del rango extraído  
- extract_window_end_utc (TIMESTAMPTZ, NOT NULL) → Fin del rango extraído  
- page_number (INT, NOT NULL) → Número de página en la extracción  
- page_size (INT, NOT NULL) → Tamaño de página en la extracción  
- request_payload (JSONB) → Parámetros de la request  

Características:  
- PK: id  
- Payload: JSONB completo de QBO  
- Metadatos: ventana, timestamps, paginación, payload de request  
- Idempotencia: garantizada con `ON CONFLICT (id) DO UPDATE`  

---

***Validaciones / Volumetría***  
Durante la ejecución, el pipeline imprime mensajes (`print`) con:  
- Filas cargadas  
- IDs únicos  
- Rango de fechas procesado  

Valida que:  
- Reejecutar el mismo rango devuelve el mismo número de filas  
- El conteo de IDs únicos coincide con filas (no hay duplicados)  
- Revisando `extract_window_start_utc` y `extract_window_end_utc` se pueden detectar huecos o solapamientos  

---

***Troubleshooting***  
- Auth (401/403): refresh token expirado → actualizar en Mage Secrets  
- Paginación: revisar startposition y maxresults  
- Rate limits (429): esperar y dejar que backoff lo maneje  
- Timezones: siempre usar UTC en parámetros y metadatos  
- Permisos: revisar credenciales de Postgres en Mage Secrets  

---

***Checklist de aceptación***  

- [x] Mage y Postgres se comunican por nombre de servicio  
- [x] Todos los secretos (QBO y Postgres) están en Mage Secrets; no hay secretos en el repo/entorno expuesto  
- [x] Pipelines `qb_<entidad>_backfill` aceptan `fecha_inicio` y `fecha_fin` (UTC) y segmentan el rango  
- [x] Trigger one-time configurado, ejecutado y luego deshabilitado/marcado como completado  
- [x] Esquema raw con tablas por entidad, payload completo y metadatos obligatorios  
- [x] Idempotencia verificada: reejecución de un tramo no genera duplicados  
- [x] Paginación y rate limits manejados y documentados  
- [x] Volumetría y validaciones mínimas registradas y archivadas como evidencia  
- [x] Runbook de reanudación y reintentos disponible y seguido  

---

***Evidencias***  
Se encuentran en la carpeta `evidencias/` con:  
- Configuración de Mage Secrets (nombres visibles, valores ocultos)  
- Triggers one-time configurados y ejecutados (completed)  
- Tablas raw con registros en pgAdmin  
- Logs de volumetría y evidencia de idempotencia  
