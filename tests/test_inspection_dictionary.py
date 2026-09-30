"""批2 字典面 red-first：专项/项目/参数/标准 CRUD + 4 junction 家族（28 端点）。

镜像 lab-springboot InspectionDictionaryService / InspectionJunctionService 语义。
每测试独立种子（conftest db_client TRUNCATE→seed）；junction save()=upsert 覆盖
全部载荷字段（含 None——JPA merge 语义）、unlink 幂等 204。
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

_T_SEED = "2026-09-30T08:00:00+00:00"


def _auth(_client: TestClient, token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# M06.F01.I01 检测专项
# ---------------------------------------------------------------------------


@pytest.mark.fn("M06.F01.I01")
def test_specialty_list_page_wrapper_and_order(db_client: TestClient, bearer: str) -> None:
    """Page 包裹不过滤语义：items=全量、page??1、pageSize??len、total=len；排序 sort_order,code。"""
    resp = db_client.get("/api/inspection/specialties", headers=_auth(db_client, bearer))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert [i["code"] for i in body["items"]] == ["SP-02", "SP-01"]  # sort_order 1<2
    assert body["page"] == 1
    assert body["pageSize"] == 2  # 缺省 = len(items)
    assert body["total"] == 2
    row = body["items"][1]
    assert row["officialNo"] == "OF-01"  # camelCase 别名序列化
    assert row["createdAt"] == _T_SEED


@pytest.mark.fn("M06.F01.I01")
def test_specialty_keyword_case_insensitive(db_client: TestClient, bearer: str) -> None:
    resp = db_client.get(
        "/api/inspection/specialties",
        params={"keyword": "混凝土"},
        headers=_auth(db_client, bearer),
    )
    assert resp.status_code == 200
    assert [i["code"] for i in resp.json()["items"]] == ["SP-01"]
    # 大小写不敏感：小写 keyword 命中大写 code
    resp = db_client.get(
        "/api/inspection/specialties",
        params={"keyword": "sp-02"},
        headers=_auth(db_client, bearer),
    )
    assert resp.status_code == 200
    assert [i["code"] for i in resp.json()["items"]] == ["SP-02"]


@pytest.mark.fn("M06.F01.I01")
def test_specialty_create_defaults_and_missing_required_400(
    db_client: TestClient, bearer: str
) -> None:
    headers = _auth(db_client, bearer)
    # 契约必填 officialNo 缺失 → 400（组合根 RequestValidationError 收口家族 400）
    resp = db_client.post(
        "/api/inspection/specialties",
        json={"code": "SP-99", "name": "缺官方编号"},
        headers=headers,
    )
    assert resp.status_code == 400, resp.text
    # 最小载荷 → 默认值镜像（isOfficial/enabled=true、sortOrder=0）
    resp = db_client.post(
        "/api/inspection/specialties",
        json={"code": "SP-99", "officialNo": "OF-99", "name": "新专项"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["code"] == "SP-99"
    assert body["isOfficial"] is True
    assert body["enabled"] is True
    assert body["sortOrder"] == 0
    assert body["createdAt"]  # UTC ISO 字符串
    assert body["createdAt"] != _T_SEED


@pytest.mark.fn("M06.F01.I01")
def test_specialty_update_partial_and_missing_404(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.put(
        "/api/inspection/specialties/SP-02",
        json={"name": "安全防护检测（改）"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "安全防护检测（改）"
    assert body["officialNo"] == "OF-02"  # 部分更新：未提及字段不动
    assert body["isOfficial"] is True
    assert body["updatedAt"] != _T_SEED
    resp = db_client.put(
        "/api/inspection/specialties/MISS",
        json={"name": "x"},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.fn("M06.F01.I01")
def test_specialty_delete_204_then_404(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    # 建一个无引用专项再删（种子 SP-01 被 OBJ-01 引用、SP-02 被 OBJ-02 引用——FK 500 路径不测）
    resp = db_client.post(
        "/api/inspection/specialties",
        json={"code": "SP-99", "officialNo": "OF-99", "name": "待删"},
        headers=headers,
    )
    assert resp.status_code == 200
    resp = db_client.delete("/api/inspection/specialties/SP-99", headers=headers)
    assert resp.status_code == 204
    resp = db_client.delete("/api/inspection/specialties/SP-99", headers=headers)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# M06.F02.I01 检测项目
# ---------------------------------------------------------------------------


@pytest.mark.fn("M06.F02.I01")
def test_object_list_filters_and_page_echo(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.get(
        "/api/inspection/objects",
        params={"inspectionSpecialtyCode": "SP-01"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert [i["code"] for i in resp.json()["items"]] == ["OBJ-01"]
    resp = db_client.get(
        "/api/inspection/objects",
        params={"keyword": "锚杆"},
        headers=headers,
    )
    assert [i["code"] for i in resp.json()["items"]] == ["OBJ-02"]
    # page/pageSize 仅回显不过滤（镜像 springboot controller 注释语义）
    resp = db_client.get(
        "/api/inspection/objects",
        params={"page": 5, "pageSize": 1},
        headers=headers,
    )
    body = resp.json()
    assert len(body["items"]) == 2
    assert body["page"] == 5
    assert body["pageSize"] == 1
    assert body["total"] == 2


@pytest.mark.fn("M06.F02.I01")
def test_object_create_defaults_and_update_delete(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.post(
        "/api/inspection/objects",
        json={
            "code": "OBJ-99",
            "inspectionSpecialtyCode": "SP-01",
            "sourceProjectNo": "P-2026-099",
            "sourceProjectName": "新工程",
            "name": "新检测项目",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["isOptionalForQualification"] is False  # 默认 false
    assert body["isOfficial"] is True
    assert body["enabled"] is True
    assert body["sortOrder"] == 0
    resp = db_client.put(
        "/api/inspection/objects/OBJ-99",
        json={"name": "新检测项目（改）"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "新检测项目（改）"
    assert resp.json()["inspectionSpecialtyCode"] == "SP-01"
    resp = db_client.delete("/api/inspection/objects/OBJ-99", headers=headers)
    assert resp.status_code == 204
    resp = db_client.delete("/api/inspection/objects/OBJ-99", headers=headers)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# M06.F02.I02 专项↔项目 + 项目↔参数关联
# ---------------------------------------------------------------------------


@pytest.mark.fn("M06.F02.I02")
def test_specialty_object_link_upsert_overwrites_payload_unlink_idempotent(
    db_client: TestClient, bearer: str
) -> None:
    headers = _auth(db_client, bearer)
    url = "/api/inspection/links/specialty-object"
    resp = db_client.post(
        url,
        json={
            "inspectionSpecialtyCode": "SP-02",
            "inspectionObjectCode": "OBJ-02",
            "remark": "新增关联",
        },
        headers=headers,
    )
    assert resp.status_code == 204, resp.text
    resp = db_client.get(url, params={"inspectionSpecialtyCode": "SP-02"}, headers=headers)
    body = resp.json()
    assert body["total"] == 1
    assert body["page"] == 1  # junction list 固定 page=1、pageSize=size
    assert body["pageSize"] == 1
    assert body["items"][0]["remark"] == "新增关联"
    # 同键再 link：save()=upsert，载荷字段全部覆盖（None 也覆盖——JPA merge 语义）
    resp = db_client.post(
        url,
        json={"inspectionSpecialtyCode": "SP-02", "inspectionObjectCode": "OBJ-02"},
        headers=headers,
    )
    assert resp.status_code == 204
    body = db_client.get(url, params={"inspectionSpecialtyCode": "SP-02"}, headers=headers).json()
    assert body["total"] == 1
    assert body["items"][0]["remark"] is None
    # unlink 幂等 204
    resp = db_client.request(
        "DELETE",
        url,
        json={"inspectionSpecialtyCode": "SP-02", "inspectionObjectCode": "OBJ-02"},
        headers=headers,
    )
    assert resp.status_code == 204
    resp = db_client.request(
        "DELETE",
        url,
        json={"inspectionSpecialtyCode": "SP-02", "inspectionObjectCode": "OBJ-02"},
        headers=headers,
    )
    assert resp.status_code == 204
    assert (
        db_client.get(url, params={"inspectionSpecialtyCode": "SP-02"}, headers=headers).json()[
            "total"
        ]
        == 0
    )


@pytest.mark.fn("M06.F02.I02")
def test_object_parameter_link_requires_level_filters_and_unlink(
    db_client: TestClient, bearer: str
) -> None:
    headers = _auth(db_client, bearer)
    url = "/api/inspection/links/object-parameter"
    # 契约必填 qualificationLevel（springboot DTO 容 null 缺省 QUALIFIED——
    # 生成契约必填，缺省路径不可达，测试显式传值；REQ 澄清记录）
    resp = db_client.post(
        url,
        json={"inspectionObjectCode": "OBJ-02", "inspectionParameterCode": "PAR-B"},
        headers=headers,
    )
    assert resp.status_code == 400, resp.text
    resp = db_client.post(
        url,
        json={
            "inspectionObjectCode": "OBJ-02",
            "inspectionParameterCode": "PAR-B",
            "qualificationLevel": "RESTRICTED",
            "sourcePage": 3,
            "remark": "限值",
        },
        headers=headers,
    )
    assert resp.status_code == 204
    # 双维过滤
    assert (
        db_client.get(url, params={"inspectionObjectCode": "OBJ-02"}, headers=headers).json()[
            "items"
        ][0]["qualificationLevel"]
        == "RESTRICTED"
    )
    assert (
        db_client.get(url, params={"inspectionParameterCode": "PAR-A"}, headers=headers).json()[
            "total"
        ]
        == 1  # 种子 (OBJ-01, PAR-A, QUALIFIED)
    )
    assert (
        db_client.get(
            url,
            params={"inspectionObjectCode": "OBJ-01", "inspectionParameterCode": "PAR-B"},
            headers=headers,
        ).json()["total"]
        == 0
    )
    # unlink 请求体不含 qualificationLevel（纯键 DTO）
    resp = db_client.request(
        "DELETE",
        url,
        json={"inspectionObjectCode": "OBJ-02", "inspectionParameterCode": "PAR-B"},
        headers=headers,
    )
    assert resp.status_code == 204
    assert (
        db_client.get(url, params={"inspectionObjectCode": "OBJ-02"}, headers=headers).json()[
            "total"
        ]
        == 0
    )


# ---------------------------------------------------------------------------
# M06.F03.I01 检测参数
# ---------------------------------------------------------------------------


@pytest.mark.fn("M06.F03.I01")
def test_parameter_list_source_type_filter_and_defaults(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.get(
        "/api/inspection/parameters",
        params={"sourceType": "custom"},
        headers=headers,
    )
    assert [i["code"] for i in resp.json()["items"]] == ["PAR-C"]
    # 最小载荷 → 默认值镜像（rawName/canonicalName=name? 契约两者必填显式传；
    # aliases=[]、sourceType=official、sortOrder=0）
    resp = db_client.post(
        "/api/inspection/parameters",
        json={
            "code": "PAR-D",
            "name": "碳化深度",
            "rawName": "碳化深度",
            "canonicalName": "碳化深度",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["sourceType"] == "official"
    assert body["aliases"] == []
    assert body["sortOrder"] == 0
    # aliases jsonb roundtrip（部分更新：其余字段不动）
    resp = db_client.put(
        "/api/inspection/parameters/PAR-D",
        json={"aliases": ["碳化值"], "unit": "mm"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["aliases"] == ["碳化值"]
    assert body["unit"] == "mm"
    assert body["name"] == "碳化深度"
    resp = db_client.delete("/api/inspection/parameters/PAR-D", headers=headers)
    assert resp.status_code == 204
    resp = db_client.delete("/api/inspection/parameters/MISS", headers=headers)
    assert resp.status_code == 404


@pytest.mark.fn("M06.F03.I01")
def test_parameter_create_missing_required_400(db_client: TestClient, bearer: str) -> None:
    resp = db_client.post(
        "/api/inspection/parameters",
        json={"code": "PAR-X", "name": "缺别名全称"},
        headers=_auth(db_client, bearer),
    )
    assert resp.status_code == 400, resp.text


# ---------------------------------------------------------------------------
# M06.F03.I02 标准↔参数关联
# ---------------------------------------------------------------------------


@pytest.mark.fn("M06.F03.I02")
def test_standard_parameter_link_flow(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    url = "/api/inspection/links/standard-parameter"
    resp = db_client.post(
        url,
        json={"inspectionStandardCode": "STD-2", "inspectionParameterCode": "PAR-C"},
        headers=headers,
    )
    assert resp.status_code == 204, resp.text
    assert (
        db_client.get(url, params={"inspectionStandardCode": "STD-2"}, headers=headers).json()[
            "total"
        ]
        == 1
    )
    assert (
        db_client.get(url, params={"inspectionParameterCode": "PAR-A"}, headers=headers).json()[
            "total"
        ]
        == 1  # 种子 (STD-1, PAR-A)
    )
    resp = db_client.request(
        "DELETE",
        url,
        json={"inspectionStandardCode": "STD-2", "inspectionParameterCode": "PAR-C"},
        headers=headers,
    )
    assert resp.status_code == 204
    resp = db_client.request(
        "DELETE",
        url,
        json={"inspectionStandardCode": "STD-2", "inspectionParameterCode": "PAR-C"},
        headers=headers,
    )
    assert resp.status_code == 204  # 幂等
    assert (
        db_client.get(url, params={"inspectionStandardCode": "STD-2"}, headers=headers).json()[
            "total"
        ]
        == 0
    )


# ---------------------------------------------------------------------------
# M06.F04.I01 检测标准
# ---------------------------------------------------------------------------


@pytest.mark.fn("M06.F04.I01")
def test_standard_list_status_filter_and_crud(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.get("/api/inspection/standards", params={"status": "active"}, headers=headers)
    assert [i["code"] for i in resp.json()["items"]] == ["STD-1"]
    resp = db_client.get(
        "/api/inspection/standards", params={"status": "superseded"}, headers=headers
    )
    assert [i["code"] for i in resp.json()["items"]] == ["STD-2"]
    resp = db_client.get("/api/inspection/standards", params={"keyword": "规范"}, headers=headers)
    assert [i["code"] for i in resp.json()["items"]] == ["STD-3"]
    # 最小载荷 → status 默认 active
    resp = db_client.post(
        "/api/inspection/standards",
        json={"code": "STD-99", "name": "新标准"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body: dict[str, Any] = resp.json()
    assert body["status"] == "active"
    assert body["sortOrder"] == 0
    resp = db_client.put(
        "/api/inspection/standards/STD-99",
        json={"status": "superseded", "version": "2025"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "superseded"
    assert body["version"] == "2025"
    assert body["name"] == "新标准"
    resp = db_client.delete("/api/inspection/standards/STD-99", headers=headers)
    assert resp.status_code == 204
    resp = db_client.delete("/api/inspection/standards/STD-99", headers=headers)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# M06.F04.I02 项目↔标准关联（role 维度）
# ---------------------------------------------------------------------------


@pytest.mark.fn("M06.F04.I02")
def test_object_standard_link_role_is_key_part(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    url = "/api/inspection/links/object-standard"
    # 种子 (OBJ-01, STD-1, JUDGMENT)；同 (object, standard) 异 role = 不同键
    resp = db_client.post(
        url,
        json={
            "inspectionObjectCode": "OBJ-01",
            "inspectionStandardCode": "STD-1",
            "role": "TESTING",
        },
        headers=headers,
    )
    assert resp.status_code == 204, resp.text
    assert (
        db_client.get(url, params={"inspectionObjectCode": "OBJ-01"}, headers=headers).json()[
            "total"
        ]
        == 2
    )
    assert [
        i["inspectionStandardCode"]
        for i in db_client.get(
            url,
            params={"inspectionObjectCode": "OBJ-01", "role": "TESTING"},
            headers=headers,
        ).json()["items"]
    ] == ["STD-1"]
    assert [
        i["inspectionStandardCode"]
        for i in db_client.get(
            url,
            params={"inspectionObjectCode": "OBJ-01", "role": "JUDGMENT"},
            headers=headers,
        ).json()["items"]
    ] == ["STD-1"]
    # unlink 带 role 键；未命中静默 no-op（幂等 204）
    resp = db_client.request(
        "DELETE",
        url,
        json={
            "inspectionObjectCode": "OBJ-01",
            "inspectionStandardCode": "STD-1",
            "role": "TESTING",
        },
        headers=headers,
    )
    assert resp.status_code == 204
    resp = db_client.request(
        "DELETE",
        url,
        json={
            "inspectionObjectCode": "OBJ-01",
            "inspectionStandardCode": "STD-1",
            "role": "TESTING",
        },
        headers=headers,
    )
    assert resp.status_code == 204
    assert (
        db_client.get(
            url,
            params={"inspectionObjectCode": "OBJ-01", "role": "TESTING"},
            headers=headers,
        ).json()["total"]
        == 0
    )
    assert (
        db_client.get(
            url,
            params={"inspectionObjectCode": "OBJ-01", "role": "JUDGMENT"},
            headers=headers,
        ).json()["total"]
        == 1  # JUDGMENT 种子行不受影响
    )


# ---------------------------------------------------------------------------
# 批2 统一镜像语义 ①：60 端点全部 require_bearer（代表性抽查五面各一）
# ---------------------------------------------------------------------------


@pytest.mark.fn("M06.F01.I01")
def test_anonymous_401_across_five_surfaces(db_client: TestClient) -> None:
    for path in (
        "/api/inspection/specialties",
        "/api/calculation-methods",
        "/api/technical-requirements",
        "/api/report-names",
        "/api/param-interfaces",
    ):
        resp = db_client.get(path)
        assert resp.status_code == 401, f"{path} → {resp.status_code}"
