import requests
from datetime import datetime, timezone, timedelta
from mage_ai.data_preparation.shared.secrets import get_secret_value
import time

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


# para sacar el access token con el refresh token
def get_access_token():
    client_id = get_secret_value('qb_client_id')
    client_secret = get_secret_value('qb_client_secret')
    refresh_token = get_secret_value('qb_refresh')

    url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    # request para sacar el access token
    response = requests.post(
        url,
        headers=headers,
        data=data,
        auth=(client_id, client_secret),
        timeout=60
    )  

    #porsi hay error
    response.raise_for_status()
    token_data = response.json()

    return token_data["access_token"]


#traigo datos del qbo
def _fetch_qb_data(realm_id, access_token, query, base_url, minor_version, start_pos=1, max_results=100):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    }

    params = {
        'query': query,
        'minorversion': minor_version,
        'startposition': start_pos,
        'maxresults': max_results
    }

    url = f"{base_url.rstrip('/')}/v3/company/{realm_id}/query"

    max_retries = 5
    backoff_time = 2

    for attempt in range(max_retries):
        try:
            # intento de request
            print(f"[Intento {attempt+1}] Request a la API: {url} con {params}")
            response = requests.get(url, headers=headers, params=params, timeout=120)

            if response.status_code == 429:  # demasiadas llamadas
                print("Limite alcanzado ahora backoff")
                time.sleep(backoff_time)
                backoff_time *= 2
                continue

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            # error en request
            print(f"Error en la API: {e}")
            time.sleep(backoff_time)
            backoff_time *= 2

    raise Exception("Reintentos máximos alcanzados al llamar a la API de QBO")


@data_loader
def load_data(*args, **kwargs):
    realm_id = get_secret_value('qb_realm')
    minor_version = 75
    base_url = 'https://sandbox-quickbooks.api.intuit.com'

    fecha_inicio = kwargs.get('fecha_inicio')
    fecha_fin = kwargs.get('fecha_fin')

    # convertir a datetime para chunking
    fecha_inicio_dt = datetime.fromisoformat(fecha_inicio.replace("Z", "+00:00")) if fecha_inicio else None
    fecha_fin_dt = datetime.fromisoformat(fecha_fin.replace("Z", "+00:00")) if fecha_fin else None

    access_token = get_access_token()
    all_data = []

    # si no defino fechas traigo toda la informacion
    if not fecha_inicio_dt or not fecha_fin_dt:
        print("No se definieron fechas, usando extracción completa sin chunking.")
        where = ""
        query = f"select * from Invoice{where} order by Metadata.LastUpdatedTime asc"

        page_size = int(kwargs.get('page_size', 100))
        start_pos = 1
        page_number = 1

        while True:
            data = _fetch_qb_data(
                realm_id, access_token, query, base_url, minor_version,
                start_pos=start_pos, max_results=page_size
            )
            invoices = data.get("QueryResponse", {}).get("Invoice", [])
            if not invoices:
                break

            now_iso = datetime.now(timezone.utc).isoformat()
            meta = {
                "extract_window_start_utc": fecha_inicio or now_iso,
                "extract_window_end_utc": fecha_fin or now_iso,
                "page_number": page_number,
                "page_size": page_size,
                "request_payload": {
                    "realm_id": realm_id,
                    "minor_version": minor_version,
                    "query": query,
                    "startposition": start_pos,
                    "maxresults": page_size,
                    "base_url": base_url,
                },
            }
            all_data.append({"data": data, "_meta": meta})

            if len(invoices) < page_size:
                break
            start_pos += page_size
            page_number += 1

        return all_data

    # chunking
    chunk_size = timedelta(days=7)
    current_start = fecha_inicio_dt

    while current_start < fecha_fin_dt:
        current_end = min(current_start + chunk_size, fecha_fin_dt)

        # query para este tramo
        where = f" WHERE Metadata.LastUpdatedTime >= '{current_start.isoformat()}' AND Metadata.LastUpdatedTime < '{current_end.isoformat()}'"
        query = f"select * from Invoice{where} order by Metadata.LastUpdatedTime asc"

        # log de chunk
        print(f"Procesando chunk: {current_start.isoformat()} → {current_end.isoformat()}")

        page_size = int(kwargs.get('page_size', 100))
        start_pos = 1
        page_number = 1
        total_rows = 0
        start_time = datetime.now(timezone.utc)

        while True:
            data = _fetch_qb_data(
                realm_id, access_token, query, base_url, minor_version,
                start_pos=start_pos, max_results=page_size
            )

            invoices = data.get("QueryResponse", {}).get("Invoice", [])
            if not invoices:  # si ya no hay más resultados
                break

            now_iso = datetime.now(timezone.utc).isoformat()
            meta = {
                "extract_window_start_utc": current_start.isoformat(),
                "extract_window_end_utc": current_end.isoformat(),
                "page_number": page_number,
                "page_size": page_size,
                "request_payload": {
                    "realm_id": realm_id,
                    "minor_version": minor_version,
                    "query": query,
                    "startposition": start_pos,
                    "maxresults": page_size,
                    "base_url": base_url,
                },
            }
            all_data.append({"data": data, "_meta": meta})
            total_rows += len(invoices)

            if len(invoices) < page_size:
                break
            start_pos += page_size
            page_number += 1

        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        # log de chunk completado
        print(f"Chunk {current_start.isoformat()} → {current_end.isoformat()} completado: "
              f"{total_rows} filas, {page_number} páginas, duración {duration:.2f}s")

        current_start = current_end

    return all_data


@test
def test_output(output, *args) -> None:
    assert output is not None, 'The output is undefined'