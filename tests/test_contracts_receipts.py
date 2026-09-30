"""批4 合同与接样 red-first（M02.F01.I01 + M03.F01.I01/I02 + M03.F09.I01）。

镜像 lab-springboot ContractService/SampleReceiptService/SampleService + 三 Mapper
+ 三 Repository + 三 Controller：
- tenant 收口（findByTenantIdAndId miss→404；复用批2 current_tenant_or_default）
- list：keyword/status/contractId/flowStatus/receiptId 过滤 + filter 三态
  （仅认 not_yet/submitted，其它值等同不传）；ORDER BY updated_at DESC（samples 用
  created_at DESC）；envelope 缺省 page=1 / pageSize=20（springboot 控制器 T11 实证，
  ⚠️ 与批3 catalog 的 pageSize??size 有意不同）
- create：contract status 缺省 active；receipt 前置校验 contract 存在（404）+
  流程默认 receiving/[]/""；sample 前置校验 receipt 存在（404）+ ext 缺省 {}；
  列表字段 null/空→[]（serializeStringList 镜像，toDto 恒回 list）
- update：部分更新 None 跳过；业务码不可改（applyUpdate 不触及 contract_code/
  contractId/receipt_id/sample_code——镜像「有意遗漏」）
- updateExt：ext 整体替换（合并是前端职责，5.89 契约必填缺省→400）
- delete：命中→204（组合根收口）/ miss→404

零种子依赖：数据全走 API create（含 receipt 的 categoryCode——先 POST report-names）。
flow 7 端点 + assign_task + history 留批5，本批不测。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

_OK = 200


def _auth(_client: TestClient, token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _switch(db_client: TestClient, token: str, tenant: str) -> str:
    resp = db_client.post(
        "/api/auth/switch-tenant",
        json={"tenantId": tenant},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == _OK, resp.text
    new: str = resp.json()["token"]
    return new


def _mk_contract(
    db_client: TestClient, headers: dict[str, str], code: str, **extra: object
) -> dict[str, object]:
    body: dict[str, object] = {
        "contractCode": code,
        "clientUnit": f"{code} 委托单位",
        "projectName": f"{code} 工程",
        "constructionUnit": "施工总承包单位",
        "witnessUnit": "见证单位",
        "witness": "见证人甲",
        **extra,
    }
    resp = db_client.post("/api/contracts", json=body, headers=headers)
    assert resp.status_code == _OK, resp.text
    row: dict[str, object] = resp.json()
    return row


def _mk_receipt(
    db_client: TestClient, headers: dict[str, str], code: str, contract_id: str, **extra: object
) -> dict[str, object]:
    body: dict[str, object] = {
        "contractId": contract_id,
        "commissionCode": code,
        "commissionDate": "2026-09-30",
        "categoryCode": "RN-B4",
        "receivedBy": "收样员甲",
        "sampleSource": "施工现场",
        "testCategory": "混凝土",
        **extra,
    }
    resp = db_client.post("/api/receipts", json=body, headers=headers)
    assert resp.status_code == _OK, resp.text
    row: dict[str, object] = resp.json()
    return row


def _mk_sample(
    db_client: TestClient, headers: dict[str, str], code: str, receipt_id: str, **extra: object
) -> dict[str, object]:
    body: dict[object, object] = {
        "receiptId": receipt_id,
        "sampleCode": code,
        **extra,
    }
    resp = db_client.post("/api/samples", json=body, headers=headers)
    assert resp.status_code == _OK, resp.text
    row: dict[str, object] = resp.json()
    return row


def _mk_category(db_client: TestClient, headers: dict[str, str], code: str = "RN-B4") -> None:
    """receipt.category_code FK → inspection_report_names：先建报告名称（零种子依赖）。"""
    resp = db_client.post(
        "/api/report-names", json={"code": code, "name": "批4 报告名称"}, headers=headers
    )
    assert resp.status_code == _OK, resp.text


# ----------------------------------------------------------------------
# M02.F01.I01 合同管理
# ----------------------------------------------------------------------


@pytest.mark.fn("M02.F01.I01")
def test_contracts_crud_roundtrip(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    row = _mk_contract(db_client, headers, "C-001")
    assert row["id"].startswith("C-")
    assert row["contractCode"] == "C-001"
    assert row["status"] == "active"  # status 缺省镜像
    assert row["tenantId"] == "TENANT-001"

    got = db_client.get(f"/api/contracts/{row['id']}", headers=headers)
    assert got.status_code == _OK, got.text
    assert got.json()["projectName"] == "C-001 工程"

    # update 部分更新：业务码不可改（applyUpdate 不触及 contractCode）
    up = db_client.put(
        f"/api/contracts/{row['id']}",
        json={"status": "archived", "contractCode": "TAMPERED"},
        headers=headers,
    )
    assert up.status_code == _OK, up.text
    up_row = up.json()
    assert up_row["status"] == "archived"
    assert up_row["contractCode"] == "C-001"  # 有意遗漏镜像

    # update miss → 404
    assert (
        db_client.put(
            "/api/contracts/C-404", json={"status": "archived"}, headers=headers
        ).status_code
        == 404
    )

    # delete：命中 204 / miss 404
    assert db_client.delete(f"/api/contracts/{row['id']}", headers=headers).status_code == 204
    assert db_client.get(f"/api/contracts/{row['id']}", headers=headers).status_code == 404
    assert db_client.delete(f"/api/contracts/{row['id']}", headers=headers).status_code == 404


@pytest.mark.fn("M02.F01.I01")
def test_contracts_list_filters(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    _mk_contract(db_client, headers, "C-01")
    _mk_contract(db_client, headers, "C-02", status="archived")
    _mk_contract(db_client, headers, "C-03", projectName="alpha 工程")

    def codes(params: dict[str, object]) -> list[str]:
        resp = db_client.get("/api/contracts", params=params, headers=headers)
        assert resp.status_code == _OK, resp.text
        body = resp.json()
        assert body["pageSize"] == 20  # 缺省 20 镜像（非 catalog 的 ??size）
        return [r["contractCode"] for r in body["items"]]

    # ORDER BY updated_at DESC, contract_code（now_iso 微秒精度下创建序即 DESC 序）
    assert codes({}) == ["C-03", "C-02", "C-01"]
    # keyword 大小写不敏感（project_name 命中）
    assert codes({"keyword": "alpha"}) == ["C-03"]
    # keyword（contract_code 命中）
    assert codes({"keyword": "c-01"}) == ["C-01"]
    # status 等值
    assert codes({"status": "archived"}) == ["C-02"]
    assert codes({"status": "active"}) == ["C-03", "C-01"]
    # 组合
    assert codes({"keyword": "c-0", "status": "archived"}) == ["C-02"]
    # 空串不过滤（n() 镜像）
    assert codes({"keyword": ""}) == ["C-03", "C-02", "C-01"]
    # 未命中
    assert codes({"keyword": "不存在"}) == []


@pytest.mark.fn("M02.F01.I01")
def test_contracts_tenant_isolation(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    c1 = _mk_contract(db_client, headers, "CT-1")

    t2 = _switch(db_client, bearer, "TENANT-002")
    h2 = _auth(db_client, t2)
    # list 隔离 + 跨租户定位 404
    assert db_client.get("/api/contracts", headers=h2).json()["total"] == 0
    assert db_client.get(f"/api/contracts/{c1['id']}", headers=h2).status_code == 404
    assert (
        db_client.put(
            f"/api/contracts/{c1['id']}", json={"status": "archived"}, headers=h2
        ).status_code
        == 404
    )
    assert db_client.delete(f"/api/contracts/{c1['id']}", headers=h2).status_code == 404
    # 跨租户同 contract_code 可并存（unique 是 (tenant, code)，PK=id 与码表 PK=code 不同）
    c2 = _mk_contract(db_client, h2, "CT-1")
    assert c2["id"] != c1["id"]
    assert c2["tenantId"] == "TENANT-002"
    assert db_client.get("/api/contracts", headers=h2).json()["total"] == 1
    assert db_client.get("/api/contracts", headers=headers).json()["total"] == 1


# ----------------------------------------------------------------------
# M03.F01.I01 接样单 CRUD
# ----------------------------------------------------------------------


@pytest.mark.fn("M03.F01.I01")
def test_receipts_crud_roundtrip(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    contract = _mk_contract(db_client, headers, "CTX-1")
    cid = str(contract["id"])

    row = _mk_receipt(
        db_client, headers, "REC-A", cid, judgmentBasis=["GB/T 50081"], projectName="批4 专项工程"
    )
    assert row["id"].startswith("R-")
    assert row["flowStatus"] == "receiving"  # 流程默认
    assert row["flowHistory"] == []  # history 空数组镜像
    assert row["result"] == ""  # ReceiptResult.EMPTY 镜像
    assert row["judgmentBasis"] == ["GB/T 50081"]
    assert row["testingBasis"] == []  # serializeStringList：null→[] 恒回 list
    assert row["testParameters"] == []

    got = db_client.get(f"/api/receipts/{row['id']}", headers=headers)
    assert got.status_code == _OK, got.text
    assert got.json()["commissionCode"] == "REC-A"

    _mk_receipt(db_client, headers, "REC-B", cid)
    lst = db_client.get("/api/receipts", headers=headers).json()
    assert [r["commissionCode"] for r in lst["items"]] == ["REC-B", "REC-A"]  # updated_at DESC

    def codes(params: dict[str, object]) -> list[str]:
        resp = db_client.get("/api/receipts", params=params, headers=headers)
        assert resp.status_code == _OK, resp.text
        return [r["commissionCode"] for r in resp.json()["items"]]

    assert codes({"contractId": cid}) == ["REC-B", "REC-A"]
    assert codes({"contractId": "R-404"}) == []
    assert codes({"flowStatus": "receiving"}) == ["REC-B", "REC-A"]
    assert codes({"flowStatus": "archived"}) == []
    assert codes({"keyword": "rec-a"}) == ["REC-A"]
    assert codes({"keyword": "批4"}) == ["REC-A"]  # project_name 侧命中（commission_code 侧见上）
    assert codes({"keyword": ""}) == ["REC-B", "REC-A"]
    assert codes({"keyword": "不存在"}) == []

    # update 部分更新：contractId 不可改（applyUpdate 不触及）
    up = db_client.put(
        f"/api/receipts/{row['id']}",
        json={"projectName": "新项目名", "contractId": "TAMPER"},
        headers=headers,
    )
    assert up.status_code == _OK, up.text
    up_row = up.json()
    assert up_row["projectName"] == "新项目名"
    assert up_row["contractId"] == cid  # 有意遗漏镜像

    # update miss → 404
    assert (
        db_client.put("/api/receipts/R-404", json={"remark": "x"}, headers=headers).status_code
        == 404
    )

    # create 前置校验：contract 不存在 → 404
    miss = db_client.post(
        "/api/receipts",
        json={
            "contractId": "NONEXIST",
            "commissionCode": "REC-X",
            "commissionDate": "2026-09-30",
            "categoryCode": "RN-B4",
            "receivedBy": "收样员甲",
            "sampleSource": "施工现场",
            "testCategory": "混凝土",
        },
        headers=headers,
    )
    assert miss.status_code == 404
    assert "Contract not found" in miss.json()["message"]

    # delete：命中 204 / miss 404
    assert db_client.delete(f"/api/receipts/{row['id']}", headers=headers).status_code == 204
    assert db_client.get(f"/api/receipts/{row['id']}", headers=headers).status_code == 404
    assert db_client.delete(f"/api/receipts/{row['id']}", headers=headers).status_code == 404


@pytest.mark.fn("M03.F01.I01")
def test_receipts_three_state_filter(db_client: TestClient, bearer: str) -> None:
    """filter 三态（5.57）：批4 无流转数据，实锚 not_yet 分支形状 + submitted 恒空。"""
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    cid = str(_mk_contract(db_client, headers, "CTX-F")["id"])
    _mk_receipt(db_client, headers, "REC-F1", cid)
    _mk_receipt(db_client, headers, "REC-F2", cid)

    def codes(params: dict[str, object]) -> list[str]:
        resp = db_client.get("/api/receipts", params=params, headers=headers)
        assert resp.status_code == _OK, resp.text
        return [r["commissionCode"] for r in resp.json()["items"]]

    # not_yet：指定环节=receiving 停在该环节 → 全中；无环节=history 空 → 全中
    assert codes({"filter": "not_yet", "flowStatus": "receiving"}) == ["REC-F2", "REC-F1"]
    assert codes({"filter": "not_yet"}) == ["REC-F2", "REC-F1"]
    # submitted：需流转数据（批5），批4 恒空
    assert codes({"filter": "submitted"}) == []
    assert codes({"filter": "submitted", "flowStatus": "receiving"}) == []
    # 其它值等同不传（原 JPQL 路径）
    assert codes({"filter": "xx"}) == ["REC-F2", "REC-F1"]
    # 空环节的 not_yet = history 空交集空环节 → 空
    assert codes({"filter": "not_yet", "flowStatus": "task_assignment"}) == []


# ----------------------------------------------------------------------
# M03.F01.I02 样品 CRUD + ext 补录
# ----------------------------------------------------------------------


@pytest.mark.fn("M03.F01.I02")
def test_samples_crud_and_ext(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    cid = str(_mk_contract(db_client, headers, "CTX-S")["id"])
    rid = str(_mk_receipt(db_client, headers, "REC-S", cid)["id"])

    s1 = _mk_sample(db_client, headers, "S-1", rid, ext={"depth": "5m"}, sampleName="试块A")
    assert s1["id"].startswith("S-")
    assert s1["ext"] == {"depth": "5m"}
    s2 = _mk_sample(db_client, headers, "S-2", rid)
    assert s2["ext"] == {}  # ext 缺省镜像

    lst = db_client.get("/api/samples", headers=headers).json()
    assert [r["sampleCode"] for r in lst["items"]] == ["S-2", "S-1"]  # created_at DESC
    assert lst["pageSize"] == 20  # envelope 缺省 20 镜像

    def codes(params: dict[str, object]) -> list[str]:
        resp = db_client.get("/api/samples", params=params, headers=headers)
        assert resp.status_code == _OK, resp.text
        return [r["sampleCode"] for r in resp.json()["items"]]

    assert codes({"receiptId": rid}) == ["S-2", "S-1"]
    assert codes({"receiptId": "R-404"}) == []
    assert codes({"keyword": "s-1"}) == ["S-1"]
    assert codes({"keyword": "试块a"}) == ["S-1"]  # sample_name 大小写不敏感
    assert codes({"keyword": ""}) == ["S-2", "S-1"]

    got = db_client.get(f"/api/samples/{s1['id']}", headers=headers)
    assert got.status_code == _OK, got.text

    # update 部分更新：receiptId/sampleCode 不可改
    up = db_client.put(
        f"/api/samples/{s1['id']}",
        json={"sampleName": "改名试块", "receiptId": "TAMPER", "sampleCode": "TAMPER"},
        headers=headers,
    )
    assert up.status_code == _OK, up.text
    up_row = up.json()
    assert up_row["sampleName"] == "改名试块"
    assert up_row["receiptId"] == rid
    assert up_row["sampleCode"] == "S-1"

    # updateExt：整体替换（合并是前端职责）
    ext = db_client.put(f"/api/samples/{s1['id']}/ext", json={"ext": {"a": "1"}}, headers=headers)
    assert ext.status_code == _OK, ext.text
    assert ext.json()["ext"] == {"a": "1"}  # 旧键 depth 被替换掉
    # 缺 ext → 契约必填 400（5.89）
    assert (
        db_client.put(f"/api/samples/{s1['id']}/ext", json={}, headers=headers).status_code == 400
    )

    # create 前置校验：receipt 不存在 → 404
    miss = db_client.post(
        "/api/samples", json={"receiptId": "NONEXIST", "sampleCode": "S-X"}, headers=headers
    )
    assert miss.status_code == 404
    assert "Receipt not found" in miss.json()["message"]

    assert db_client.delete(f"/api/samples/{s1['id']}", headers=headers).status_code == 204
    assert db_client.get(f"/api/samples/{s1['id']}", headers=headers).status_code == 404

    # 接样/样品 tenant 隔离（AC-6）：跨租户 list 不可见 + 跨租户 FK 引用 create 404
    t2 = _switch(db_client, bearer, "TENANT-002")
    h2 = _auth(db_client, t2)
    assert db_client.get("/api/samples", headers=h2).json()["total"] == 0
    assert db_client.get("/api/receipts", headers=h2).json()["total"] == 0
    cross = db_client.post(
        "/api/samples", json={"receiptId": rid, "sampleCode": "S-CROSS"}, headers=h2
    )
    assert cross.status_code == 404  # 他人租户 receipt miss → 404
    assert "Receipt not found" in cross.json()["message"]


# ----------------------------------------------------------------------
# M03.F09.I01 接样单详情面
# ----------------------------------------------------------------------


@pytest.mark.fn("M03.F09.I01")
def test_receipt_detail_view(db_client: TestClient, bearer: str) -> None:
    """详情 = GET receipt 全字段 + GET samples?receiptId= 清单（检测数据归批5）。"""
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    contract = _mk_contract(
        db_client,
        headers,
        "CTD-1",
        projectLocation="项目现场",
        entrustedDate="2026-09-01",
    )
    row = _mk_receipt(
        db_client,
        headers,
        "REC-D",
        str(contract["id"]),
        projectName="详情工程",
        clientUnit="详情委托单位",
        witness="见证人乙",
        judgmentBasis=["GB/T 50081", "JGJ/T 23"],
        testingBasis=["GB 50204"],
        testParameters=["抗压强度"],
    )
    _mk_sample(db_client, headers, "SD-2", row["id"])
    _mk_sample(db_client, headers, "SD-1", row["id"], sampleName="详情试块")

    detail = db_client.get(f"/api/receipts/{row['id']}", headers=headers)
    assert detail.status_code == _OK, detail.text
    body = detail.json()
    assert body["id"] == row["id"]
    assert body["contractId"] == contract["id"]
    assert body["commissionCode"] == "REC-D"
    assert body["categoryCode"] == "RN-B4"
    assert body["projectName"] == "详情工程"
    assert body["judgmentBasis"] == ["GB/T 50081", "JGJ/T 23"]
    assert body["testingBasis"] == ["GB 50204"]
    assert body["testParameters"] == ["抗压强度"]
    assert body["flowStatus"] == "receiving"
    assert body["flowHistory"] == []
    assert body["result"] == ""
    assert "lastSubmittedBy" not in body  # null 字段不落 JSON（NON_NULL 镜像，同 issuedAt）
    assert "issuedAt" not in body  # null 可选字段 exclude_none 不落 JSON（家族 to_dict 形状）

    samples = db_client.get("/api/samples", params={"receiptId": str(row["id"])}, headers=headers)
    assert samples.status_code == _OK, samples.text
    s_body = samples.json()
    assert [r["sampleCode"] for r in s_body["items"]] == ["SD-1", "SD-2"]  # created_at DESC
    assert s_body["total"] == 2
    assert s_body["items"][0]["ext"] == {}  # 样品信息齐备（ext 缺省 {}）
