import pytest


@pytest.mark.asyncio
async def test_filter_dates_empty(client):
    resp = await client.get("/filter/dates")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_filter_machines_empty(client):
    resp = await client.get("/filter/machines", params={"date_from": "2025-12-02", "date_to": "2025-12-07"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_filter_recipes_empty(client):
    resp = await client.get("/filter/recipes", params={"date_from": "2025-12-02", "date_to": "2025-12-07",  "station": "AOI-01"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_filter_lots_empty(client):
    resp = await client.get("/filter/lots", params={"date_from": "2025-12-02", "date_to": "2025-12-07", "station": "AOI-01", "product": "PKG-A"})
    assert resp.status_code == 200

