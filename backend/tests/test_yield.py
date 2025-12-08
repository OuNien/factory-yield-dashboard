# backend/tests/test_yield.py
import pytest


@pytest.mark.asyncio
async def test_yield_list_empty(client):
    resp = await client.get("/yield/list")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
