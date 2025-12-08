# backend/tests/test_auth_router.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, admin_user):
    """
    正確帳密可以登入，會拿到 access_token / token_type / role
    """
    resp = await client.post(
        "/auth/login",
        data={
            "username": admin_user["obj"].username,
            "password": admin_user["password"],
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == admin_user["obj"].username
    assert data["role"] == admin_user["obj"].role


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, admin_user):
    """
    密碼錯誤要回 400
    """
    resp = await client.post(
        "/auth/login",
        data={
            "username": admin_user["obj"].username,
            "password": "wrong_password",
        },
    )

    assert resp.status_code == 400
    body = resp.json()
    # 你 router 裡的錯誤訊息是 "Incorrect username or password"
    assert "Incorrect username or password" in body["detail"]


@pytest.mark.asyncio
async def test_me_with_token(client: AsyncClient, admin_user):
    """
    帶 token 呼叫 /auth/me，可以拿到當前使用者資訊
    """
    # 先登入拿 token
    login_resp = await client.post(
        "/auth/login",
        data={
            "username": admin_user["obj"].username,
            "password": admin_user["password"],
        },
    )
    token = login_resp.json()["access_token"]

    resp = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == admin_user["obj"].username
    assert data["role"] == admin_user["obj"].role
