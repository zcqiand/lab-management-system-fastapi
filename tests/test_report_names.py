"""批2 报告名称 red-first（M06.F07）：CRUD + get + extFields jsonb 模板 + 三关联家族。

镜像 lab-springboot InspectionReportNameService / InspectionJunctionService：
14 端点；standard 关联带 role（键部件）；junction save()=upsert 覆盖载荷含
None、unlink 幂等 204、list Page 包裹固定 page=1/pageSize=size。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _auth(_client: TestClient, token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# M06.F07.I01 CRUD + extFields
# ---------------------------------------------------------------------------


@pytest.mark.fn("M06.F07.I01")
def test_list_page_and_keyword(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.get("/api/report-names", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert [i["code"] for i in body["items"]] == ["RN-01", "RN-02"]
    assert body["total"] == 2
    resp = db_client.get("/api/report-names", params={"keyword": "锚杆"}, headers=headers)
    assert [i["code"] for i in resp.json()["items"]] == ["RN-02"]
    resp = db_client.get("/api/report-names", params={"keyword": "rn-01"}, headers=headers)
    assert [i["code"] for i in resp.json()["items"]] == ["RN-01"]


@pytest.mark.fn("M06.F07.I01")
def test_get_and_ext_fields_roundtrip(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.get("/api/report-names/RN-01", headers=headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["fullName"] == "检测报告（2026）抗字第0001号"
    ext = body["extFields"]
    assert ext is not None and len(ext) == 2
    assert ext[0] == {
        "key": "castDate",
        "label": "浇筑日期",
        "type": "date",
        "required": True,
        "options": None,
        "tag": None,
        "source": "sample",
    }
    assert ext[1]["options"] == ["C25", "C30", "C35"]
    assert body["templatePath"] == "templates/compression.docx"
    resp = db_client.get("/api/report-names/MISS", headers=headers)
    assert resp.status_code == 404


@pytest.mark.fn("M06.F07.I01")
def test_create_defaults_and_ext_fields_payload(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.post(
        "/api/report-names",
        json={"code": "RN-99", "name": "新报告"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["sortOrder"] == 0
    assert body["extFields"] is None
    resp = db_client.post(
        "/api/report-names",
        json={
            "code": "RN-98",
            "name": "钢筋报告",
            "extFields": [
                {
                    "key": "diameter",
                    "label": "直径",
                    "type": "text",
                    "required": True,
                    "options": None,
                    "tag": None,
                    "source": "sample",
                },
                {
                    "key": "count",
                    "label": "数量",
                    "type": "number",
                    "required": False,
                    "options": None,
                    "tag": "aux",
                    "source": "receipt",
                },
                {
                    "key": "grade",
                    "label": "等级",
                    "type": "select",
                    "required": True,
                    "options": ["HRB400", "HRB500"],
                    "tag": None,
                    "source": None,
                },
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()["extFields"]) == 3  # jsonb 直转 roundtrip
    resp = db_client.get("/api/report-names/RN-98", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["extFields"][1]["source"] == "receipt"


@pytest.mark.fn("M06.F07.I01")
def test_update_partial_and_missing_404(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.put(
        "/api/report-names/RN-02",
        json={"summaryName": "抗拔汇总"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["summaryName"] == "抗拔汇总"
    assert body["name"] == "锚杆抗拔检测报告"  # 部分更新
    assert body["extFields"] == []  # 种子值不动
    resp = db_client.put("/api/report-names/MISS", json={"name": "x"}, headers=headers)
    assert resp.status_code == 404


@pytest.mark.fn("M06.F07.I01")
def test_delete_204_then_404(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    resp = db_client.post(
        "/api/report-names",
        json={"code": "RN-97", "name": "待删"},
        headers=headers,
    )
    assert resp.status_code == 200
    resp = db_client.delete("/api/report-names/RN-97", headers=headers)
    assert resp.status_code == 204
    resp = db_client.delete("/api/report-names/RN-97", headers=headers)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# M06.F07.I02 三关联家族
# ---------------------------------------------------------------------------


@pytest.mark.fn("M06.F07.I02")
def test_object_report_name_links(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    url = "/api/report-names/links/object"
    resp = db_client.post(
        url,
        json={
            "inspectionObjectCode": "OBJ-02",
            "reportNameCode": "RN-02",
            "remark": "锚杆报告挂项目",
        },
        headers=headers,
    )
    assert resp.status_code == 204, resp.text
    assert (
        db_client.get(url, params={"inspectionObjectCode": "OBJ-02"}, headers=headers).json()[
            "total"
        ]
        == 1
    )
    assert (
        db_client.get(url, params={"reportNameCode": "RN-01"}, headers=headers).json()["total"]
        == 1  # 种子 (OBJ-01, RN-01)
    )
    resp = db_client.request(
        "DELETE",
        url,
        json={"inspectionObjectCode": "OBJ-02", "reportNameCode": "RN-02"},
        headers=headers,
    )
    assert resp.status_code == 204
    resp = db_client.request(
        "DELETE",
        url,
        json={"inspectionObjectCode": "OBJ-02", "reportNameCode": "RN-02"},
        headers=headers,
    )
    assert resp.status_code == 204  # 幂等
    assert (
        db_client.get(url, params={"inspectionObjectCode": "OBJ-02"}, headers=headers).json()[
            "total"
        ]
        == 0
    )


@pytest.mark.fn("M06.F07.I02")
def test_report_name_parameter_links_upsert_overwrites(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    url = "/api/report-names/links/parameter"
    resp = db_client.post(
        url,
        json={"reportNameCode": "RN-02", "inspectionParameterCode": "PAR-B", "remark": "初版"},
        headers=headers,
    )
    assert resp.status_code == 204, resp.text
    body = db_client.get(url, params={"reportNameCode": "RN-02"}, headers=headers).json()
    assert body["total"] == 1
    assert body["items"][0]["remark"] == "初版"
    # 同键再 link 空 remark → 覆盖为 None（JPA merge 载荷覆盖语义）
    resp = db_client.post(
        url,
        json={"reportNameCode": "RN-02", "inspectionParameterCode": "PAR-B"},
        headers=headers,
    )
    assert resp.status_code == 204
    body = db_client.get(url, params={"reportNameCode": "RN-02"}, headers=headers).json()
    assert body["total"] == 1
    assert body["items"][0]["remark"] is None
    resp = db_client.request(
        "DELETE",
        url,
        json={"reportNameCode": "RN-02", "inspectionParameterCode": "PAR-B"},
        headers=headers,
    )
    assert resp.status_code == 204
    assert (
        db_client.get(url, params={"reportNameCode": "RN-02"}, headers=headers).json()["total"] == 0
    )


@pytest.mark.fn("M06.F07.I02")
def test_report_name_standard_links_role_key(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    url = "/api/report-names/links/standard"
    # 种子 (RN-01, STD-1, JUDGMENT)；同对标准异 role = 不同键
    resp = db_client.post(
        url,
        json={"reportNameCode": "RN-01", "inspectionStandardCode": "STD-2", "role": "TESTING"},
        headers=headers,
    )
    assert resp.status_code == 204, resp.text
    assert (
        db_client.get(url, params={"reportNameCode": "RN-01"}, headers=headers).json()["total"] == 2
    )
    assert (
        db_client.get(
            url,
            params={"reportNameCode": "RN-01", "role": "TESTING"},
            headers=headers,
        ).json()["items"][0]["inspectionStandardCode"]
        == "STD-2"
    )
    assert (
        db_client.get(
            url,
            params={"reportNameCode": "RN-01", "role": "JUDGMENT"},
            headers=headers,
        ).json()["items"][0]["remark"]
        == "判据"
    )
    resp = db_client.request(
        "DELETE",
        url,
        json={"reportNameCode": "RN-01", "inspectionStandardCode": "STD-2", "role": "TESTING"},
        headers=headers,
    )
    assert resp.status_code == 204
    resp = db_client.request(
        "DELETE",
        url,
        json={"reportNameCode": "RN-01", "inspectionStandardCode": "STD-2", "role": "TESTING"},
        headers=headers,
    )
    assert resp.status_code == 204  # 幂等
    assert (
        db_client.get(
            url,
            params={"reportNameCode": "RN-01", "role": "TESTING"},
            headers=headers,
        ).json()["total"]
        == 0
    )
    assert (
        db_client.get(
            url,
            params={"reportNameCode": "RN-01", "role": "JUDGMENT"},
            headers=headers,
        ).json()["total"]
        == 1
    )
