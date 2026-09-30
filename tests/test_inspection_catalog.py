"""批3 基础数据 red-first（M04.F06-F09.I01）：码表 4 实体同构 CRUD（16 端点）。

镜像 lab-springboot CatalogService + InspectionCatalogMapper + 各 Repository：
- tenant 收口（findByTenantIdAndCode miss→404；复用批2 current_tenant_or_default）
- list filter JPQL 镜像：objectCode null/""→不过滤（n() + `'' OR 等值`）；keyword
  null/""→不过滤、非空 lower contains code/name；ORDER BY sort_order, code；
  Page 包裹（page??1 / pageSize??size / total=size，items 恒全量不分页）
- create = JPA save() merge：撞 (tenant, code) 全字段覆盖**含 createdAt 刷新**
  （批2 字典面实体 create 同款先例；junction 的 upsert_junction 才保留 created_at）
- update 部分更新（None 跳过）+ updatedAt=now，无空载荷 400 特判（镜像 applyUpdate 原样）
- delete miss→404 / 命中→204（组合根收口）

PG PK=code 单键（springboot CatalogEntryKey 复合键在 PG 侧不可表达——REQ-2026-003
同款 schema 事实）：跨租户同 code 不可并存，测试用异 code 验隔离。
零种子依赖：数据全走 API create（conftest grades 种子行占 C25/C30，用例避开）。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _auth(_client: TestClient, token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _switch(db_client: TestClient, token: str, tenant: str) -> str:
    resp = db_client.post(
        "/api/auth/switch-tenant",
        json={"tenantId": tenant},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    new: str = resp.json()["token"]
    return new


# ----------------------------------------------------------------------
# M04.F09.I01 牌号码表（brands）
# ----------------------------------------------------------------------


@pytest.mark.fn("M04.F09.I01")
def test_brands_crud_roundtrip(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    # create：默认值镜像（tenantId=当前租户、缺省 sortOrder=0）
    r1 = db_client.post(
        "/api/catalog/brands",
        json={
            "code": "BRD-01",
            "name": "混凝土牌号",
            "inspectionObjectCode": "OBJ-01",
            "remark": "R1",
            "sortOrder": 2,
        },
        headers=headers,
    )
    assert r1.status_code == 200, r1.text
    row = r1.json()
    assert row["code"] == "BRD-01"
    assert row["tenantId"] == "TENANT-001"
    assert row["name"] == "混凝土牌号"
    assert row["inspectionObjectCode"] == "OBJ-01"
    assert row["remark"] == "R1"
    assert row["sortOrder"] == 2
    assert row["createdAt"]
    assert row["updatedAt"]

    r2 = db_client.post(
        "/api/catalog/brands", json={"code": "BRD-02", "name": "钢筋牌号"}, headers=headers
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["sortOrder"] == 0  # 缺省镜像

    # list：ORDER BY sort_order, code → BRD-02(0) 在前
    lst = db_client.get("/api/catalog/brands", headers=headers).json()
    assert [r["code"] for r in lst["items"]] == ["BRD-02", "BRD-01"]

    # update 部分更新：None 字段不动
    up = db_client.put("/api/catalog/brands/BRD-01", json={"name": "改名"}, headers=headers)
    assert up.status_code == 200, up.text
    up_row = up.json()
    assert up_row["name"] == "改名"
    assert up_row["remark"] == "R1"  # None 跳过
    assert up_row["sortOrder"] == 2

    # update miss → 404
    assert (
        db_client.put(
            "/api/catalog/brands/BRD-404", json={"name": "x"}, headers=headers
        ).status_code
        == 404
    )

    # create 撞 (tenant, code) = JPA save() merge：全字段覆盖含 createdAt 刷新
    first_created = up_row["createdAt"]
    merge = db_client.post(
        "/api/catalog/brands",
        json={"code": "BRD-01", "name": "重创建", "sortOrder": 5},
        headers=headers,
    )
    assert merge.status_code == 200, merge.text
    m_row = merge.json()
    assert m_row["name"] == "重创建"
    assert m_row["sortOrder"] == 5
    assert "remark" not in m_row  # 载荷 None 覆盖（merge 全字段）+ NON_NULL 不落 JSON
    assert "inspectionObjectCode" not in m_row
    assert m_row["createdAt"] != first_created  # merge 刷新 createdAt
    lst2 = db_client.get("/api/catalog/brands", headers=headers).json()
    assert lst2["total"] == 2  # 未新增行

    # delete：命中 204 / miss 404
    assert db_client.delete("/api/catalog/brands/BRD-01", headers=headers).status_code == 204
    assert db_client.delete("/api/catalog/brands/BRD-01", headers=headers).status_code == 404
    assert db_client.get("/api/catalog/brands", headers=headers).json()["total"] == 1


@pytest.mark.fn("M04.F09.I01")
def test_brands_list_filters(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    rows = [
        {"code": "BRD-A", "name": "Alpha 系列", "inspectionObjectCode": "OBJ-01", "sortOrder": 2},
        {"code": "BRD-B", "name": "beta", "inspectionObjectCode": "OBJ-01", "sortOrder": 1},
        {"code": "BRD-C", "name": "Alpha 二代", "inspectionObjectCode": "OBJ-02", "sortOrder": 0},
    ]
    for body in rows:
        resp = db_client.post("/api/catalog/brands", json=body, headers=headers)
        assert resp.status_code == 200, resp.text

    def codes(params: dict[str, object]) -> list[str]:
        resp = db_client.get("/api/catalog/brands", params=params, headers=headers)
        assert resp.status_code == 200, resp.text
        return [r["code"] for r in resp.json()["items"]]

    # ORDER BY sort_order, code
    assert codes({}) == ["BRD-C", "BRD-B", "BRD-A"]
    # inspectionObjectCode 等值
    assert codes({"inspectionObjectCode": "OBJ-01"}) == ["BRD-B", "BRD-A"]
    # keyword 大小写不敏感（name 命中）
    assert codes({"keyword": "alpha"}) == ["BRD-C", "BRD-A"]
    # keyword（code 命中）
    assert codes({"keyword": "brd-b"}) == ["BRD-B"]
    # 组合
    assert codes({"inspectionObjectCode": "OBJ-01", "keyword": "beta"}) == ["BRD-B"]
    # 空串不过滤（镜像 JPQL `:keyword = ''` OR 分支）
    assert codes({"keyword": ""}) == ["BRD-C", "BRD-B", "BRD-A"]
    assert codes({"inspectionObjectCode": ""}) == ["BRD-C", "BRD-B", "BRD-A"]
    # 未命中
    assert codes({"keyword": "不存在"}) == []


# ----------------------------------------------------------------------
# M04.F07.I01 规格码表（specs）：分页包裹语义
# ----------------------------------------------------------------------


@pytest.mark.fn("M04.F07.I01")
def test_specs_pagination_wrapper(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    for code in ("SPEC-1", "SPEC-2", "SPEC-3"):
        resp = db_client.post(
            "/api/catalog/specs", json={"code": code, "name": f"规格{code}"}, headers=headers
        )
        assert resp.status_code == 200, resp.text

    bare = db_client.get("/api/catalog/specs", headers=headers)
    assert bare.status_code == 200, bare.text
    body = bare.json()
    assert body["page"] == 1  # page??1
    assert body["pageSize"] == 3  # pageSize??list.size()
    assert body["total"] == 3
    assert len(body["items"]) == 3

    paged = db_client.get(
        "/api/catalog/specs", params={"page": 2, "pageSize": 2}, headers=headers
    ).json()
    assert paged["page"] == 2
    assert paged["pageSize"] == 2
    assert paged["total"] == 3
    assert len(paged["items"]) == 3  # items 恒全量（分页参数不作过滤，批2 同款）


# ----------------------------------------------------------------------
# M04.F08.I01 等级码表（grades）：默认值 + 契约 400
# ----------------------------------------------------------------------


@pytest.mark.fn("M04.F08.I01")
def test_grades_defaults_and_missing_400(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    # 契约必填缺失 → 校验层 400（家族 ErrorResponse 收口，非 422）
    assert db_client.post("/api/catalog/grades", json={}, headers=headers).status_code == 400
    assert (
        db_client.post("/api/catalog/grades", json={"code": "GRD-1"}, headers=headers).status_code
        == 400
    )

    ok = db_client.post(
        "/api/catalog/grades", json={"code": "GRD-1", "name": "C40"}, headers=headers
    )
    assert ok.status_code == 200, ok.text
    row = ok.json()
    assert row["tenantId"] == "TENANT-001"
    assert row["sortOrder"] == 0
    assert "inspectionObjectCode" not in row
    assert "remark" not in row
    # 避开种子占用的 C25/C30（PK=code 单键）；GRD-1 可见
    lst = db_client.get("/api/catalog/grades", headers=headers).json()
    assert [r["code"] for r in lst["items"]] == ["GRD-1"]

    # blank 字段镜像 requireNonBlank → 400
    assert (
        db_client.post(
            "/api/catalog/grades", json={"code": "", "name": "x"}, headers=headers
        ).status_code
        == 400
    )


# ----------------------------------------------------------------------
# M04.F06.I01 型号码表（models）：tenant 隔离
# ----------------------------------------------------------------------


@pytest.mark.fn("M04.F06.I01")
def test_models_tenant_isolation(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    mk = db_client.post(
        "/api/catalog/models",
        json={"code": "MOD-1", "name": "TENANT-001 型号"},
        headers=headers,
    )
    assert mk.status_code == 200, mk.text

    t2 = _switch(db_client, bearer, "TENANT-002")
    h2 = _auth(db_client, t2)
    # list 隔离：只见本租户
    assert db_client.get("/api/catalog/models", headers=h2).json()["total"] == 0
    # update/delete 跨租户 miss → 404（findByTenantIdAndCode 语义）
    assert (
        db_client.put("/api/catalog/models/MOD-1", json={"name": "偷改"}, headers=h2).status_code
        == 404
    )
    assert db_client.delete("/api/catalog/models/MOD-1", headers=h2).status_code == 404
    # TENANT-002 自建行互不可见（PK=code 单键，跨租户异 code）
    mk2 = db_client.post(
        "/api/catalog/models",
        json={"code": "MOD-2", "name": "TENANT-002 型号"},
        headers=h2,
    )
    assert mk2.status_code == 200, mk2.text
    assert mk2.json()["tenantId"] == "TENANT-002"
    assert db_client.get("/api/catalog/models", headers=h2).json()["total"] == 1
    mine = db_client.get("/api/catalog/models", headers=headers).json()
    assert [r["code"] for r in mine["items"]] == ["MOD-1"]
