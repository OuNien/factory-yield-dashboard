# backend/tests/test_user_router.py
import pytest
from httpx import AsyncClient
from app.models.user import User, Role
from app.auth.security import hash_password


@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient, db_session):
    username = "ut_user_1"
    password = "ut_password"
    role = "engineer"

    # 確保事前不存在
    user = await db_session.get(User, username)
    if user:
        await db_session.delete(user)
        await db_session.commit()

    resp = await client.post(
        "/user/add",
        params={"username": username, "password": password, "role": role},
    )

    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    # DB 裡應該有這個 user
    user = await db_session.get(User, username)
    assert user is not None
    assert user.username == username
    assert user.role == Role.engineer


@pytest.mark.asyncio
async def test_create_user_conflict(client: AsyncClient, db_session):
    """
    再次建立同帳號，應該會 400
    """
    username = "ut_user_2"
    password = "ut_password"
    role = "viewer"

    # 先插入一個
    exists = await db_session.get(User, username)
    if not exists:
        exists = User(
            username=username,
            password_hash=hash_password(password),
            role=Role.viewer,
        )
        db_session.add(exists)
        await db_session.commit()

    resp = await client.post(
        "/user/add",
        params={"username": username, "password": password, "role": role},
    )

    assert resp.status_code == 400
    body = resp.json()
    assert "already exists" in body["detail"]


@pytest.mark.asyncio
async def test_list_user(client: AsyncClient):
    """
    簡單測一下 /user/list 有正常回傳 list
    """
    resp = await client.get("/user/list")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_update_and_delete_user(client: AsyncClient, db_session):
    username = "ut_user_3"
    original_password = "old_pw"
    new_password = "new_pw"

    # 先插一個 user
    user = await db_session.get(User, username)
    if not user:
        user = User(
            username=username,
            password_hash=hash_password(original_password),
            role=Role.viewer,
        )
        db_session.add(user)
        await db_session.commit()

    # 更新 user（注意：你的 router 裡 payload 欄位叫 password_hash）
    resp_update = await client.put(
        f"/user/update/{username}",
        json={"password_hash": new_password, "role": "admin"},
    )
    assert resp_update.status_code == 200
    body = resp_update.json()
    assert body["status"] == "updated"

    await db_session.refresh(user)
    assert user.role == Role.admin

    # 刪除
    resp_delete = await client.delete(f"/user/delete/{username}")
    assert resp_delete.status_code == 200
    assert resp_delete.json()["status"] == "deleted"

    deleted = await db_session.get(User, username)
    assert deleted is None
