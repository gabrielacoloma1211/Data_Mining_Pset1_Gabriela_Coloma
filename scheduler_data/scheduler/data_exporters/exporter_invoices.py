import psycopg2
import json
from mage_ai.data_preparation.shared.secrets import get_secret_value

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter


@data_exporter
def export_invoices(data, *args, **kwargs):
    """
    Inserta registros en la tabla raw.qb_invoices en Postgres con UPSERT (idempotente).
    Crea el esquema y la tabla si no existen.
    """

    #conexion con postgres
    conn = psycopg2.connect(
        host=get_secret_value('pg_host'),
        port=get_secret_value('pg_port'),
        dbname=get_secret_value('pg_db'),
        user=get_secret_value('pg_user'),
        password=get_secret_value('pg_password')
    )
    cursor = conn.cursor()

    # crea la tabla si no existe ya
    cursor.execute("""
    CREATE SCHEMA IF NOT EXISTS raw;

    CREATE TABLE IF NOT EXISTS raw.qb_invoices (
        id TEXT PRIMARY KEY,
        payload JSONB NOT NULL,
        ingested_at_utc TIMESTAMPTZ NOT NULL,
        extract_window_start_utc TIMESTAMPTZ NOT NULL,
        extract_window_end_utc TIMESTAMPTZ NOT NULL,
        page_number INT NOT NULL,
        page_size INT NOT NULL,
        request_payload JSONB
    );
    """)

    #agarro el dataframe y lo paso a dict
    if hasattr(data, "to_dict"):
        rows = data.to_dict(orient="records")
    else:
        rows = data

    # upsert osea que si no hay inserta y si sí hay actualiza
    for row in rows:
        cursor.execute("""
            INSERT INTO raw.qb_invoices (
                id, payload, ingested_at_utc, extract_window_start_utc,
                extract_window_end_utc, page_number, page_size, request_payload
            )
            VALUES (%s, %s::jsonb, %s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (id) DO UPDATE SET
                payload = EXCLUDED.payload,
                ingested_at_utc = EXCLUDED.ingested_at_utc,
                extract_window_start_utc = EXCLUDED.extract_window_start_utc,
                extract_window_end_utc = EXCLUDED.extract_window_end_utc,
                page_number = EXCLUDED.page_number,
                page_size = EXCLUDED.page_size,
                request_payload = EXCLUDED.request_payload;
        """, (
            row["id"],
            json.dumps(row["payload"]),
            row["ingested_at_utc"],
            row["extract_window_start_utc"],
            row["extract_window_end_utc"],
            row["page_number"],
            row["page_size"],
            json.dumps(row["request_payload"]),
        ))

    conn.commit()
    cursor.close()
    conn.close()