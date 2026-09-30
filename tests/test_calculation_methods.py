"""批2 计算方法 red-first（M06.F05.I01）：复合主键 (object, parameter)，平台级，裸 List。

镜像 lab-springboot CalculationMethodService 语义：契约返裸 List（无 Page 包裹）、
双键过滤、排序 sort_order + 双键、默认 algorithmType=manual / specimenCount=1。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _auth(_client: TestClient, token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.fn("M06.F05.I01")
def test_list_returns_bare_array_with_dual_filters(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.get("/api/calculation-methods", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list)  # 契约裸 List，非 Page 包裹
    assert len(body) == 1
    assert body[0]["inspectionObjectCode"] == "OBJ-01"
    assert body[0]["inspectionParameterCode"] == "PAR-A"
    assert body[0]["algorithmType"] == "manual"
    assert body[0]["formula"] == "R = P/A"
    # 双键过滤
    assert (
        len(
            db_client.get(
                "/api/calculation-methods",
                params={"inspectionObjectCode": "OBJ-01"},
                headers=headers,
            ).json()
        )
        == 1
    )
    assert (
        db_client.get(
            "/api/calculation-methods",
            params={"inspectionObjectCode": "OBJ-02"},
            headers=headers,
        ).json()
        == []
    )
    assert (
        len(
            db_client.get(
                "/api/calculation-methods",
                params={"inspectionObjectCode": "OBJ-01", "inspectionParameterCode": "PAR-B"},
                headers=headers,
            ).json()
        )
        == 0
    )


@pytest.mark.fn("M06.F05.I01")
def test_get_by_composite_key_and_missing_404(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.get("/api/calculation-methods/OBJ-01/PAR-A", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["roundingRule"] == "0.1"
    resp = db_client.get("/api/calculation-methods/OBJ-02/PAR-A", headers=headers)
    assert resp.status_code == 404


@pytest.mark.fn("M06.F05.I01")
def test_create_defaults(db_client: TestClient, bearer: str) -> None:
    resp = db_client.post(
        "/api/calculation-methods",
        json={"inspectionObjectCode": "OBJ-02", "inspectionParameterCode": "PAR-B"},
        headers=_auth(db_client, bearer),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["algorithmType"] == "manual"  # 默认 manual
    assert body["specimenCount"] == 1  # 默认 1
    assert body["sortOrder"] == 0
    assert "testingStandardCode" not in body  # null 不落 JSON（NON_NULL 镜像）
    # 复合主键可见
    resp = db_client.get("/api/calculation-methods/OBJ-02/PAR-B", headers=_auth(db_client, bearer))
    assert resp.status_code == 200


@pytest.mark.fn("M06.F05.I01")
def test_update_partial_and_missing_404(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.put(
        "/api/calculation-methods/OBJ-01/PAR-A",
        json={"formula": "R = F/A", "specimenCount": 3},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["formula"] == "R = F/A"
    assert body["specimenCount"] == 3
    assert body["algorithmType"] == "manual"  # 未提及字段不动
    assert body["conditions"] == "标准养护 28d"
    assert body["updatedAt"] != "2026-09-30T08:00:00+00:00"
    resp = db_client.put(
        "/api/calculation-methods/OBJ-02/PAR-A",
        json={"formula": "x"},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.fn("M06.F05.I01")
def test_delete_204_then_404(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.delete("/api/calculation-methods/OBJ-01/PAR-A", headers=headers)
    assert resp.status_code == 204
    resp = db_client.delete("/api/calculation-methods/OBJ-01/PAR-A", headers=headers)
    assert resp.status_code == 404
