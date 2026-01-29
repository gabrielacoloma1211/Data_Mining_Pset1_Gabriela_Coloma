from datetime import datetime, timezone
import pandas as pd
import json

if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data, *args, **kwargs):
    """
    Template code for a transformer block.

    Add more parameters to this function if this block has multiple parent blocks.
    There should be one parameter for each output variable from each parent block.

    Args:
        data: The output from the upstream parent block
        args: The output from any additional upstream blocks (if applicable)

    Returns:
        Anything (e.g. data frame, dictionary, array, int, str, etc.)
    """
    # Specify your transformation logic here

    #separo
    if isinstance(data, dict) and "_meta" in data:
        kwargs = {**data.get("_meta", {}), **kwargs}   
        data = data.get("data", data)                  

    now_utc = datetime.now(timezone.utc)

    extract_start = kwargs.get('extract_window_start_utc') or now_utc.isoformat()
    extract_end   = kwargs.get('extract_window_end_utc')   or now_utc.isoformat()
    page_number   = int(kwargs.get('page_number', 1))
    page_size     = int(kwargs.get('page_size', 100))
    request_payload = kwargs.get('request_payload') or {}

    # veo cual entidad estoy trabajando
    qr = (data or {}).get('QueryResponse', {}) if isinstance(data, dict) else {}

    entity_key = kwargs.get('entity_key')
    if not entity_key:
        for k in ('Invoice', 'Customer', 'Item'):
            if k in qr:
                entity_key = k
                break

    records = qr.get(entity_key, []) if entity_key else []

    # Ajusta paginacion porsi
    try:
        page_size_resp = int(qr.get('maxResults', page_size))
        start_pos = int(qr.get('startPosition', 1))
        if page_size_resp > 0:
            page_number = 1 + (max(1, start_pos) - 1) // page_size_resp
            page_size = page_size_resp
    except Exception:
        pass

    # construye filas
    rows = []
    for rec in records or []:
        rec_id = str(rec.get('Id')) if isinstance(rec, dict) else None
        if not rec_id:
            continue
        rows.append({
            "id": rec_id,
            "payload": json.dumps(rec),  
            "ingested_at_utc": now_utc.isoformat(),
            "extract_window_start_utc": extract_start,
            "extract_window_end_utc": extract_end,
            "page_number": page_number,
            "page_size": page_size,
            "request_payload": request_payload,
        })

    return pd.DataFrame(rows)


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'