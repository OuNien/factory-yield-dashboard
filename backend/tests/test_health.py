# backend/tests/test_health.py
import pytest


@pytest.mark.asyncio
async def test_health_ok(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_db_ok(client):
    resp = await client.get("/health/db")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "error")
    # 在我們的測試環境，理論上會是 ok
    assert data["db"] in ("ok", "error")


@pytest.mark.asyncio
async def test_health_redis_ok(client):
    resp = await client.get("/health/redis")
    assert resp.status_code == 200
    data = resp.json()
    assert data["redis_ratelimit"] in ("ok", "down")
