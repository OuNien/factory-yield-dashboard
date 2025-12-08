# backend/tests/test_lot.py
import pytest


@pytest.mark.asyncio
async def test_add_lot_and_list(client):
    # 建立一個 lot
    resp = await client.post(
        "/add",
        params={
            "lot_id": "LOT001",
            "product": "P1",
            "station": "ST1",
            "total": 100,
            "good": 95,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"

    # 讀取 lot list
    resp2 = await client.get("/list")
    assert resp2.status_code == 200
    lots = resp2.json()
    assert isinstance(lots, list)
    # 至少會有剛剛那顆 LOT001
    assert any(l["lot_id"] == "LOT001" for l in lots)
