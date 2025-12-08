# backend/tests/test_lot_router.py
import pytest
from httpx import AsyncClient
from app.models.lot import Lot
from app.models.yield_record import YieldRecord


@pytest.mark.asyncio
async def test_add_and_list_lot(client: AsyncClient, db_session):
    lot_id = "UT_LOT_001"

    # 先清除舊資料
    lot = await db_session.get(Lot, lot_id)
    if lot:
        await db_session.delete(lot)
        await db_session.commit()

    resp_add = await client.post(
        "/add",
        params={
            "lot_id": lot_id,
            "product": "PKG-UT",
            "station": "AOI-UT",
            "total": 1000,
            "good": 950,
        },
    )
    assert resp_add.status_code == 200
    assert resp_add.json()["status"] == "ok"

    # /list 應該包含這個 lot（這邊只檢查不為空）
    resp_list = await client.get("/list")
    assert resp_list.status_code == 200
    data = resp_list.json()
    assert isinstance(data, list)
    assert any(item["lot_id"] == lot_id for item in data)


@pytest.mark.asyncio
async def test_update_lot(client: AsyncClient, db_session):
    lot_id = "UT_LOT_002"

    # 確保先有一筆 lot
    lot = await db_session.get(Lot, lot_id)
    if not lot:
        lot = Lot(
            lot_id=lot_id,
            product="PKG-OLD",
            station="AOI-OLD",
            total=100,
            good=80,
        )
        db_session.add(lot)
        await db_session.commit()

    # 更新 total / good
    resp_update = await client.put(
        f"/update/{lot_id}",
        json={
            "total": 200,
            "good": 180,
        },
    )
    assert resp_update.status_code == 200
    body = resp_update.json()
    assert body["status"] == "updated"
    assert body["lot_id"] == lot_id

    await db_session.refresh(lot)
    assert lot.total == 200
    assert lot.good == 180


@pytest.mark.asyncio
async def test_delete_lot_with_and_without_yield_record(
    client: AsyncClient,
    db_session,
):
    """
    - 如果這個 lot 有被 yield_record reference，delete 應該 400
    - 沒有被 reference，delete 應該成功
    """
    lot_id_used = "UT_LOT_USED"
    lot_id_free = "UT_LOT_FREE"

    # 建立一個有被 yield_record 使用的 lot
    lot_used = await db_session.get(Lot, lot_id_used)
    if not lot_used:
        lot_used = Lot(
            lot_id=lot_id_used,
            product="PKG-A",
            station="AOI-A",
            total=100,
            good=90,
        )
        db_session.add(lot_used)
        await db_session.commit()

    yr = await db_session.execute(
        db_session.sync_session.query(YieldRecord).filter(
            YieldRecord.lot_id == lot_id_used
        )
    )
    # 上面那行 sync_session 的寫法很醜，也可以改成純 async 版；
    # 這邊先簡化，實務上你可以直接用 async select。

    # 乾脆保證自己插一筆 yield_record 比較保險：
    yr_obj = YieldRecord(
        lot_id=lot_id_used,
        total=100,
        good=90,
        yield_rate=90.0,
    )
    db_session.add(yr_obj)
    await db_session.commit()

    # 刪除這個 lot 應該會 400
    resp_delete_used = await client.delete(f"/delete/{lot_id_used}")
    assert resp_delete_used.status_code == 400
    assert "referenced by yield_record" in resp_delete_used.json()["detail"]

    # 建一個沒有被 reference 的 lot
    lot_free = await db_session.get(Lot, lot_id_free)
    if not lot_free:
        lot_free = Lot(
            lot_id=lot_id_free,
            product="PKG-B",
            station="AOI-B",
            total=50,
            good=49,
        )
        db_session.add(lot_free)
        await db_session.commit()

    resp_delete_free = await client.delete(f"/delete/{lot_id_free}")
    assert resp_delete_free.status_code == 200
    body = resp_delete_free.json()
    assert body["status"] == "deleted"
    assert body["lot_id"] == lot_id_free

    deleted = await db_session.get(Lot, lot_id_free)
    assert deleted is None
