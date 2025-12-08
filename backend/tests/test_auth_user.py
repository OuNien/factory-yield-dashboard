# backend/tests/test_auth_user.py
import pytest


ADMIN_USER = "admin_test"
ADMIN_PASS = "secret123"


@pytest.mark.asyncio
async def test_create_user_and_list(client):
    # 建立一個 admin 帳號
    resp = await client.post(
        "/user/add",
        params={
            "username": ADMIN_USER,
            "password": ADMIN_PASS,
            "role": "admin",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    # create_user 回傳 {"status": "ok"}
    assert data.get("status") == "ok"

    # 確認 /user/list 有資料
    resp2 = await client.get("/user/list")
    assert resp2.status_code == 200
    users = resp2.json()
    assert isinstance(users, list)
    # 至少要有一個 user
    assert any(u["username"] == ADMIN_USER for u in users)


@pytest.mark.asyncio
async def test_login_success_and_me(client):
    # 先確保 user 存在（可以重覆呼叫沒關係）
    await client.post(
        "/user/add",
        params={
            "username": ADMIN_USER,
            "password": ADMIN_PASS,
            "role": "admin",
        },
    )

    # 登入：使用 OAuth2PasswordRequestForm → form-data/x-www-form-urlencoded
    resp = await client.post(
        "/auth/login",
        data={
            "username": ADMIN_USER,
            "password": ADMIN_PASS,
            "grant_type": "password",
        },
    )
    assert resp.status_code == 200
    token_data = resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # 帶著 token 呼叫 /auth/me
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    resp_me = await client.get("/auth/me", headers=headers)
    assert resp_me.status_code == 200
    me = resp_me.json()
    assert me["username"] == ADMIN_USER
    assert me["role"] == "admin"


@pytest.mark.asyncio
async def test_login_fail(client):
    resp = await client.post(
        "/auth/login",
        data={
            "username": "not_exist",
            "password": "wrong",
            "grant_type": "password",
        },
    )
    # 你的實作是 400 Incorrect username or password
    assert resp.status_code in (400, 401)
