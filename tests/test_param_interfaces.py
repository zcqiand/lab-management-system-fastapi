"""批2 参数界面 red-first（M06.F08）：CRUD + get + config jsonb + 参数↔界面 link。

镜像 lab-springboot ParamInterfaceService / InspectionJunctionService：8 端点；
link 行 reportNameCode/config 可空 jsonb，upsert 覆盖载荷含 None，unlink 幂等 204。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _auth(_client: TestClient, token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# M06.F08.I01 CRUD + config jsonb
# ---------------------------------------------------------------------------


@pytest.mark.fn("M06.F08.I01")
def test_list_page_keyword_and_page_echo(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.get("/api/param-interfaces", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert [i["code"] for i in body["items"]] == ["PI-1", "PI-2"]
    assert body["total"] == 2
    assert body["page"] == 1
    resp = db_client.get("/api/param-interfaces", params={"keyword": "抗压"}, headers=headers)
    assert [i["code"] for i in resp.json()["items"]] == ["PI-1"]
    # page/pageSize 仅回显不过滤
    resp = db_client.get(
        "/api/param-interfaces", params={"page": 3, "pageSize": 10}, headers=headers
    )
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["page"] == 3
    assert body["pageSize"] == 10


@pytest.mark.fn("M06.F08.I01")
def test_get_and_config_roundtrip(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.get("/api/param-interfaces/PI-1", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["config"] == {"columns": 3, "grid": True}  # jsonb 直转
    assert body["isOfficial"] is True
    assert body["componentPath"] == "views/records/CompressionForm"
    resp = db_client.get("/api/param-interfaces/MISS", headers=headers)
    assert resp.status_code == 404


@pytest.mark.fn("M06.F08.I01")
def test_create_defaults_and_config_payload(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.post(
        "/api/param-interfaces",
        json={"code": "PI-99", "componentPath": "views/records/NewForm"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["isOfficial"] is True  # 默认 true
    assert body["sortOrder"] == 0
    assert "config" not in body
    assert "name" not in body  # 契约可空；null 不落 JSON（NON_NULL 镜像）
    resp = db_client.post(
        "/api/param-interfaces",
        json={
            "code": "PI-98",
            "componentPath": "views/records/GridForm",
            "name": "网格界面",
            "config": {"columns": 2, "mode": "edit"},
        },
        headers=headers,
    )
    assert resp.status_code == 200
    resp = db_client.get("/api/param-interfaces/PI-98", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["config"] == {"columns": 2, "mode": "edit"}


@pytest.mark.fn("M06.F08.I01")
def test_update_partial_and_missing_404(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.put(
        "/api/param-interfaces/PI-2",
        json={"name": "抗拔界面（改）", "config": {"layout": "grid2"}},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "抗拔界面（改）"
    assert body["config"] == {"layout": "grid2"}
    assert body["componentPath"] == "views/records/AnchorForm"  # 未提及字段不动
    resp = db_client.put("/api/param-interfaces/MISS", json={"name": "x"}, headers=headers)
    assert resp.status_code == 404


@pytest.mark.fn("M06.F08.I01")
def test_delete_204_then_404(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.post(
        "/api/param-interfaces",
        json={"code": "PI-97", "componentPath": "views/records/TempForm"},
        headers=headers,
    )
    assert resp.status_code == 200
    resp = db_client.delete("/api/param-interfaces/PI-97", headers=headers)
    assert resp.status_code == 204
    resp = db_client.delete("/api/param-interfaces/PI-97", headers=headers)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# M06.F08.I02 参数↔界面 link
# ---------------------------------------------------------------------------


@pytest.mark.fn("M06.F08.I02")
def test_param_interface_link_upsert_unlink_idempotent(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    url = "/api/param-interfaces/links"
    # 种子 (PAR-A, PI-1, RN-1, config={"mode":"auto"})
    assert (
        db_client.get(url, params={"paramInterfaceCode": "PI-1"}, headers=headers).json()["total"]
        == 1
    )
    resp = db_client.post(
        url,
        json={"inspectionParameterCode": "PAR-B", "paramInterfaceCode": "PI-2", "config": {"w": 1}},
        headers=headers,
    )
    assert resp.status_code == 204, resp.text
    body = db_client.get(url, params={"inspectionParameterCode": "PAR-B"}, headers=headers).json()
    assert body["total"] == 1
    assert body["items"][0]["config"] == {"w": 1}
    assert "reportNameCode" not in body["items"][0]  # NON_NULL 镜像
    # 同键再 link：config=None 覆盖既有 config（载荷含 None 覆盖）
    resp = db_client.post(
        url,
        json={
            "inspectionParameterCode": "PAR-B",
            "paramInterfaceCode": "PI-2",
            "reportNameCode": "RN-02",
        },
        headers=headers,
    )
    assert resp.status_code == 204
    body = db_client.get(url, params={"inspectionParameterCode": "PAR-B"}, headers=headers).json()
    assert body["total"] == 1
    assert "config" not in body["items"][0]  # None 覆盖后不落 JSON（NON_NULL 镜像）
    assert body["items"][0]["reportNameCode"] == "RN-02"
    # unlink 幂等
    resp = db_client.request(
        "DELETE",
        url,
        json={"inspectionParameterCode": "PAR-B", "paramInterfaceCode": "PI-2"},
        headers=headers,
    )
    assert resp.status_code == 204
    resp = db_client.request(
        "DELETE",
        url,
        json={"inspectionParameterCode": "PAR-B", "paramInterfaceCode": "PI-2"},
        headers=headers,
    )
    assert resp.status_code == 204
    assert (
        db_client.get(url, params={"inspectionParameterCode": "PAR-B"}, headers=headers).json()[
            "total"
        ]
        == 0
    )
    assert (
        db_client.get(url, params={"paramInterfaceCode": "PI-1"}, headers=headers).json()["total"]
        == 1  # 种子行不受影响
    )
