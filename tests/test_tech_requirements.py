"""批2 技术要求 red-first（M06.F06.I01）：业务三键 + tenant 收口，平台裸 List。

镜像 lab-springboot TechnicalRequirementService + currentTenantIdOrDefault()：
claim tenant_id 非空用之，否则 directory 默认租户 TENANT-001（目录配置非字面量
兜底，ADR-0019 合规）。种子：同三键双租户行（TENANT-001 verified min30 /
TENANT-002 draft min25）。

契约差异点（REQ 澄清记录，2026-10-01 批6 CT live 修正）：springboot Mapper 缺省
comparison=RequirementComparison.u，wire 值是 "≥"（u/u2 是 Java 枚举对 ≥/≤ 的
转义名）——fastapi 照镜像缺失落 "≥"（旧判「无 'u' 成员缺省 400」误把 Java 名当
wire 值，已废）。valueType/judgmentMode/verificationStatus 契约可空，默认路径
可达（numeric/manual/draft 镜像）。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

_TRIPLE = "/api/technical-requirements/OBJ-01/PAR-A/STD-1"


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


@pytest.mark.fn("M06.F06.I01")
def test_list_bare_array_and_filters(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.get("/api/technical-requirements", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list)  # 裸 List
    assert len(body) == 1  # alice 无 tenant claim → TENANT-001 → 只见 verified 行
    row = body[0]
    assert row["tenantId"] == "TENANT-001"
    assert row["verificationStatus"] == "verified"
    assert row["minValue"] == 30
    assert row["comparison"] == "≥"
    assert row["grade"] == "C30"
    # 四维过滤
    assert (
        len(
            db_client.get(
                "/api/technical-requirements",
                params={"verificationStatus": "draft"},
                headers=headers,
            ).json()
        )
        == 0  # draft 行是 TENANT-002 的
    )
    assert (
        len(
            db_client.get(
                "/api/technical-requirements",
                params={"inspectionParameterCode": "PAR-A"},
                headers=headers,
            ).json()
        )
        == 1
    )
    assert (
        db_client.get(
            "/api/technical-requirements",
            params={"judgmentStandardCode": "STD-2"},
            headers=headers,
        ).json()
        == []
    )
    assert (
        len(
            db_client.get(
                "/api/technical-requirements",
                params={"inspectionObjectCode": "OBJ-01", "inspectionParameterCode": "PAR-A"},
                headers=headers,
            ).json()
        )
        == 1
    )


@pytest.mark.fn("M06.F06.I01")
def test_tenant_isolation_and_default_tenant_fallback(db_client: TestClient, bearer: str) -> None:
    # 默认租户：无 claim → TENANT-001
    resp = db_client.get(_TRIPLE, headers=_auth(db_client, bearer))
    assert resp.status_code == 200
    assert resp.json()["tenantId"] == "TENANT-001"
    # 切换租户 → TENANT-002 行（draft min25，异三键：PG PK 三键下同三键
    # 跨租户不可并存——REQ 澄清记录）
    token2 = _switch(db_client, bearer, "TENANT-002")
    resp = db_client.get("/api/technical-requirements", headers=_auth(db_client, token2))
    body = resp.json()
    assert len(body) == 1
    assert body[0]["tenantId"] == "TENANT-002"
    assert body[0]["inspectionParameterCode"] == "PAR-B"
    assert body[0]["minValue"] == 25
    assert body[0]["verificationStatus"] == "draft"
    # tenant 隔离：TENANT-002 看不见 TENANT-001 的同三键行 → 404
    resp = db_client.get(_TRIPLE, headers=_auth(db_client, token2))
    assert resp.status_code == 404


@pytest.mark.fn("M06.F06.I01")
def test_get_by_triple_key_and_missing_404(db_client: TestClient, bearer: str) -> None:
    resp = db_client.get(_TRIPLE, headers=_auth(db_client, bearer))
    assert resp.status_code == 200
    assert resp.json()["unit"] == "MPa"
    assert resp.json()["clause"] == "6.3.1"
    resp = db_client.get(
        "/api/technical-requirements/OBJ-01/PAR-A/STD-2",
        headers=_auth(db_client, bearer),
    )
    assert resp.status_code == 404


@pytest.mark.fn("M06.F06.I01")
def test_create_defaults_and_comparison_default(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    # comparison 缺失 → 镜像 springboot Mapper 缺省 RequirementComparison.u（wire "≥"）
    # ——2026-10-01 批6 CT live 修正：旧判「契约无 'u' 成员」误把 Java 枚举名当 wire 值
    resp = db_client.post(
        "/api/technical-requirements",
        json={
            "inspectionObjectCode": "OBJ-02",
            "inspectionParameterCode": "PAR-B",
            "judgmentStandardCode": "STD-1",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["comparison"] == "≥"
    # valueType/judgmentMode/verificationStatus 缺省可达（镜像 numeric/manual/draft）
    resp = db_client.post(
        "/api/technical-requirements",
        json={
            "inspectionObjectCode": "OBJ-02",
            "inspectionParameterCode": "PAR-B",
            "judgmentStandardCode": "STD-1",
            "comparison": "≤",
            "maxValue": 5,
            "unit": "mm",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tenantId"] == "TENANT-001"  # 落 directory 默认租户
    assert body["valueType"] == "numeric"
    assert body["judgmentMode"] == "manual"
    assert body["verificationStatus"] == "draft"
    assert body["sortOrder"] == 0
    resp = db_client.get("/api/technical-requirements/OBJ-02/PAR-B/STD-1", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["maxValue"] == 5


@pytest.mark.fn("M06.F06.I01")
def test_update_partial_and_missing_404(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.put(
        _TRIPLE,
        json={"verificationStatus": "reviewed", "minValue": 35},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["verificationStatus"] == "reviewed"
    assert body["minValue"] == 35
    assert body["valueType"] == "numeric"  # 未提及字段不动
    assert body["comparison"] == "≥"
    assert body["tenantId"] == "TENANT-001"
    resp = db_client.put(
        "/api/technical-requirements/OBJ-01/PAR-A/STD-2",
        json={"minValue": 1},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.fn("M06.F06.I01")
def test_delete_204_then_404_scoped_to_tenant(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    # 先建（新三键），再删
    resp = db_client.post(
        "/api/technical-requirements",
        json={
            "inspectionObjectCode": "OBJ-02",
            "inspectionParameterCode": "PAR-B",
            "judgmentStandardCode": "STD-3",
            "comparison": "=",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    url = "/api/technical-requirements/OBJ-02/PAR-B/STD-3"
    resp = db_client.delete(url, headers=headers)
    assert resp.status_code == 204
    resp = db_client.delete(url, headers=headers)
    assert resp.status_code == 404
