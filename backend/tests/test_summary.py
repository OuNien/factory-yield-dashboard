import pytest


@pytest.mark.asyncio
async def test_summary_list_empty(client):
    resp = await client.get("/summary/list")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
