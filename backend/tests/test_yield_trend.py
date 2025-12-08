import pytest
from app.database.mongo import mongo_db


@pytest.mark.asyncio
async def test_yield_trend_basic(client):
    coll = mongo_db["yield_trend"]
    coll.docs = [
        {"lot_id": "L1", "yield": 92, "ts": 1},
        {"lot_id": "L1", "yield": 93, "ts": 2},
    ]

    resp = await client.get(
        "/yield/trend",
        params={"date_from": "2025-11-30", "date_to": "2025-12-06", "station": "AOI-01", "product": "PKG-A", "lots": "LOT01000"}
    )
    assert resp.status_code == 200
