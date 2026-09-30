"""批5 试验过程流 red-first（REQ-2026-006）：receipts act 7 + history + task + test-records 6。

镜像 lab-springboot ReportFlowService / SampleReceiptService / TestRecordService：
- act 七端点：operator 双层 400（先于 per-id 循环）；逐条 ok/err 批量 HTTP 恒 200；
  SUBMIT_NEXT 链 receiving→task_assignment→data_entry→review→approval→issuance→archived；
  RETURN_PREV 严格反向；WITHDRAW 仅 receiving 自转移写 history；archived 特例仅 SUBMIT
  自转移 audit（reason 缺省 "archived: post-archive audit"）；history 条目六键恒在、
  reason null→""；SUBMIT 写 lastSubmittedBy、WITHDRAW 清空、RETURN 保留
- assignTask：三字段 None 跳过 + updatedAt 恒刷；仅 RECEIVING 推进 task_assignment 且
  history operator=assigneeName（lastSubmittedBy 同值）；任何 stage 可 assign
- history 端点：空→[]、miss→404、跨租户→404
- test-records：envelope page??1/pageSize??20 + 仅 sampleId 过滤（parameterCode 接受不过滤，
  springboot controller 接受后不传 service 的镜像）；TR- 前缀；六字段部分更新
  （sample_id 业务键不可改）；verdict 改判；delete 204
- 三态 filter submitted 分支深测（锚定批4 _three_state 镜像谓词：带环节时须
  flow_status != 环节 且 history 有 submit-from-环节；不带环节=history 非空且
  lastSubmittedBy 非空；not_yet 带环节=flow_status==环节，无 history 条件）
零种子依赖：数据全走 API create（FK 所需 parameter 先 POST /api/inspection/parameters）。
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

_OK = 200

# stage wire 值 → act 路由段（assigning/data-entry/approve ≠ 枚举值，REQ-2026-006 澄清第 3 条）
_ACT_PATH = {
    "receiving": "receiving",
    "task_assignment": "assigning",
    "data_entry": "data-entry",
    "review": "review",
    "approval": "approve",
    "issuance": "issuance",
    "archived": "archived",
}
_CHAIN = [
    "receiving",
    "task_assignment",
    "data_entry",
    "review",
    "approval",
    "issuance",
    "archived",
]


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


def _mk_category(db_client: TestClient, headers: dict[str, str], code: str = "RN-B4") -> None:
    """receipt.category_code FK → inspection_report_names：先建报告名称（零种子依赖）。"""
    resp = db_client.post(
        "/api/report-names", json={"code": code, "name": "批5 报告名称"}, headers=headers
    )
    assert resp.status_code == _OK, resp.text


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


def _mk_parameter(db_client: TestClient, headers: dict[str, str], code: str = "PAR-B5") -> None:
    """test_records.parameter_code FK → inspection_parameters（RESTRICT）：先建参数。"""
    resp = db_client.post(
        "/api/inspection/parameters",
        json={
            "code": code,
            "name": "批5 参数",
            "rawName": "批5 参数",
            "canonicalName": "批5 参数",
        },
        headers=headers,
    )
    assert resp.status_code == _OK, resp.text


def _mk_sample(
    db_client: TestClient, headers: dict[str, str], code: str, receipt_id: str, **extra: object
) -> dict[str, object]:
    body: dict[str, object] = {
        "receiptId": receipt_id,
        "sampleCode": code,
        **extra,
    }
    resp = db_client.post("/api/samples", json=body, headers=headers)
    assert resp.status_code == _OK, resp.text
    row: dict[str, object] = resp.json()
    return row


def _mk_record(
    db_client: TestClient, headers: dict[str, str], sample_id: str, **extra: object
) -> dict[str, object]:
    body: dict[str, object] = {
        "sampleId": sample_id,
        "parameterCode": "PAR-B5",
        "requirement": "≥30MPa",
        "result": "35.2",
        **extra,
    }
    resp = db_client.post("/api/test-records", json=body, headers=headers)
    assert resp.status_code == _OK, resp.text
    row: dict[str, object] = resp.json()
    return row


def _act(
    db_client: TestClient,
    headers: dict[str, str],
    stage_path: str,
    ids: list[str],
    action: str,
    operator: str,
    reason: str | None = None,
) -> list[dict[str, object]]:
    payload: dict[str, object] = {"ids": ids, "action": action, "operator": operator}
    if reason is not None:
        payload["reason"] = reason
    resp = db_client.post(f"/api/receipts/{stage_path}/act", json=payload, headers=headers)
    assert resp.status_code == _OK, resp.text
    body: list[dict[str, object]] = resp.json()
    return body


def _to_stage(db_client: TestClient, headers: dict[str, str], rid: str, target: str) -> None:
    """沿 SUBMIT 链把 receipt 推到 target stage（每步 operator=op-<stage>）。"""
    i = _CHAIN.index(target)
    for stage in _CHAIN[:i]:
        _act(
            db_client,
            headers,
            _ACT_PATH[stage],
            [rid],
            "submit",
            f"op-{stage}",
        )


def _get(db_client: TestClient, headers: dict[str, str], rid: str) -> dict[str, object]:
    resp = db_client.get(f"/api/receipts/{rid}", headers=headers)
    assert resp.status_code == _OK, resp.text
    body: dict[str, object] = resp.json()
    return body


# ----------------------------------------------------------------------
# M03.F01.I03 / F02.I02 / F03.I02 / F05.I01 / F06.I01 / F07.I01 act 面
# ----------------------------------------------------------------------


@pytest.mark.fn("M03.F01.I03")
def test_act_submit_chain_all_stages(db_client: TestClient, bearer: str) -> None:
    """SUBMIT 链全走：ok 形状 + history 六键 + lastSubmittedBy 演进。"""
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    cid = str(_mk_contract(db_client, headers, "C5-CH")["id"])
    rid = str(_mk_receipt(db_client, headers, "REC-CH", cid)["id"])
    fresh = _get(db_client, headers, rid)
    assert "lastSubmittedBy" not in fresh  # None 不落 JSON（NON_NULL 镜像）

    for stage, nxt in zip(_CHAIN[:-1], _CHAIN[1:], strict=True):
        results = _act(db_client, headers, _ACT_PATH[stage], [rid], "submit", f"op-{stage}")
        assert results == [
            {"id": rid, "ok": True, "flowStatus": nxt}
        ]  # ok 项无 message 键（NON_NULL 镜像）

    body = _get(db_client, headers, rid)
    assert body["flowStatus"] == "archived"
    assert body["lastSubmittedBy"] == "op-issuance"
    hist: list[dict[str, object]] = body["flowHistory"]  # type: ignore[assignment]
    assert len(hist) == 6
    assert [h["operator"] for h in hist] == [f"op-{s}" for s in _CHAIN[:-1]]
    for entry, frm, to in zip(hist, _CHAIN[:-1], _CHAIN[1:], strict=True):
        assert set(entry.keys()) == {"action", "from", "to", "operator", "at", "reason"}
        assert entry["action"] == "submit"
        assert entry["from"] == frm and entry["to"] == to
        assert entry["reason"] == ""  # null→""（js() 镜像，六键恒在）


@pytest.mark.fn("M03.F02.I02")
def test_act_return_chain_and_withdraw_reject(db_client: TestClient, bearer: str) -> None:
    """RETURN 反向链 + WITHDRAW 仅 receiving。"""
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    cid = str(_mk_contract(db_client, headers, "C5-RT")["id"])
    rid = str(_mk_receipt(db_client, headers, "REC-RT", cid)["id"])

    # RETURN 无前驱拒
    results = _act(db_client, headers, "receiving", [rid], "return", "op-rt")
    assert results == [
        {"id": rid, "ok": False, "message": "Invalid transition from receiving with return"}
    ]
    assert _get(db_client, headers, rid)["flowStatus"] == "receiving"

    # RETURN 反向链从 issuance 起步（archived 仅接受 submit，返回归 test_act_archived_special）
    _to_stage(db_client, headers, rid, "issuance")
    for stage, prev in zip(reversed(_CHAIN[1:-1]), reversed(_CHAIN[:-2]), strict=True):
        results = _act(db_client, headers, _ACT_PATH[stage], [rid], "return", f"rt-{stage}")
        assert results[0]["ok"] is True
        assert results[0]["flowStatus"] == prev
    assert _get(db_client, headers, rid)["lastSubmittedBy"] == "op-approval"  # RETURN 保留

    # WITHDRAW 仅 receiving：task_assignment 上拒
    _act(db_client, headers, "receiving", [rid], "submit", "op-again")
    results = _act(db_client, headers, "assigning", [rid], "withdraw", "op-wd")
    assert results == [
        {"id": rid, "ok": False, "message": "Invalid transition from task_assignment with withdraw"}
    ]
    assert _get(db_client, headers, rid)["flowStatus"] == "task_assignment"


@pytest.mark.fn("M03.F03.I02")
def test_act_stage_mismatch_and_notfound(db_client: TestClient, bearer: str) -> None:
    """stage 不符 / miss 的 err 文案逐字；err 项无 flowStatus 键；不写 history。"""
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    cid = str(_mk_contract(db_client, headers, "C5-MM")["id"])
    rid = str(_mk_receipt(db_client, headers, "REC-MM", cid)["id"])

    results = _act(db_client, headers, "data-entry", [rid], "submit", "op-mm")
    assert results == [
        {
            "id": rid,
            "ok": False,
            "message": "Stage mismatch: requires data_entry but is receiving",
        }
    ]  # err 项无 flowStatus 键

    # 批量混合：stage 不符 + miss，逐条 err 不中断，HTTP 200（_act 已断言）
    results = _act(db_client, headers, "data-entry", [rid, "R-MISS"], "submit", "op-mm")
    assert [r["ok"] for r in results] == [False, False]
    assert results[1]["message"] == "Receipt not found: R-MISS"
    assert _get(db_client, headers, rid)["flowHistory"] == []  # err 不写 history


@pytest.mark.fn("M03.F05.I01")
def test_act_batch_partial_failure(db_client: TestClient, bearer: str) -> None:
    """批量逐条 ok/err：单条失败不中断批，命中者照常推进。"""
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    cid = str(_mk_contract(db_client, headers, "C5-BT")["id"])
    r1 = str(_mk_receipt(db_client, headers, "REC-B1", cid)["id"])
    r2 = str(_mk_receipt(db_client, headers, "REC-B2", cid)["id"])
    r3 = str(_mk_receipt(db_client, headers, "REC-B3", cid)["id"])
    _to_stage(db_client, headers, r1, "review")
    _to_stage(db_client, headers, r2, "review")

    results = _act(db_client, headers, "review", [r1, "R-MISS", r3], "submit", "op-bt")
    assert results == [
        {"id": r1, "ok": True, "flowStatus": "approval"},
        {"id": "R-MISS", "ok": False, "message": "Receipt not found: R-MISS"},
        {
            "id": r3,
            "ok": False,
            "message": "Stage mismatch: requires review but is receiving",
        },
    ]
    assert _get(db_client, headers, r1)["flowStatus"] == "approval"  # 命中者照常推进
    assert _get(db_client, headers, r3)["flowHistory"] == []


@pytest.mark.fn("M03.F06.I01")
def test_act_approve_stage_gate(db_client: TestClient, bearer: str) -> None:
    """approve act（M03.F06）：stage gate 逐字 + approval 上 submit 推进 issuance。"""
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    cid = str(_mk_contract(db_client, headers, "C5-AP")["id"])
    rid = str(_mk_receipt(db_client, headers, "REC-AP", cid)["id"])

    # stage gate：非 approval 单调 approve act → err 文案逐字（err 项无 flowStatus 键）
    results = _act(db_client, headers, "approve", [rid], "submit", "op-ap")
    assert results == [
        {"id": rid, "ok": False, "message": "Stage mismatch: requires approval but is receiving"}
    ]

    # approval 上 submit → issuance：ok 形状 + history 条目 + lastSubmittedBy 写 operator
    _to_stage(db_client, headers, rid, "approval")
    results = _act(db_client, headers, "approve", [rid], "submit", "审批员乙")
    assert results == [{"id": rid, "ok": True, "flowStatus": "issuance"}]
    body = _get(db_client, headers, rid)
    assert body["lastSubmittedBy"] == "审批员乙"
    hist: list[dict[str, object]] = body["flowHistory"]  # type: ignore[assignment]
    assert hist[-1] == {
        "action": "submit",
        "from": "approval",
        "to": "issuance",
        "operator": "审批员乙",
        "at": hist[-1]["at"],
        "reason": "",
    }


@pytest.mark.fn("M03.F07.I01")
def test_act_issuance_stage_gate(db_client: TestClient, bearer: str) -> None:
    """issuance act（M03.F07）：stage gate 逐字 + issuance 上 submit 推进 archived（终态）。"""
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    cid = str(_mk_contract(db_client, headers, "C5-IS")["id"])
    rid = str(_mk_receipt(db_client, headers, "REC-IS", cid)["id"])

    results = _act(db_client, headers, "issuance", [rid], "submit", "op-is")
    assert results == [
        {"id": rid, "ok": False, "message": "Stage mismatch: requires issuance but is receiving"}
    ]

    _to_stage(db_client, headers, rid, "issuance")
    results = _act(db_client, headers, "issuance", [rid], "submit", "发放员丙")
    assert results == [{"id": rid, "ok": True, "flowStatus": "archived"}]
    body = _get(db_client, headers, rid)
    assert body["flowStatus"] == "archived"
    assert body["lastSubmittedBy"] == "发放员丙"
    hist: list[dict[str, object]] = body["flowHistory"]  # type: ignore[assignment]
    assert hist[-1]["from"] == "issuance" and hist[-1]["to"] == "archived"
    assert hist[-1]["operator"] == "发放员丙"


@pytest.mark.fn("M03.F01.I03")
def test_act_operator_two_layer_400(db_client: TestClient, bearer: str) -> None:
    """operator 双层 400（先于 per-id 循环整批拒）：缺省→校验层；空串→impl 镜像 IAE。"""
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    cid = str(_mk_contract(db_client, headers, "C5-OP")["id"])
    rid = str(_mk_receipt(db_client, headers, "REC-OP", cid)["id"])

    # 第一层：operator 契约必填缺省 → 校验层 400（批3 422→400 收口）
    resp = db_client.post(
        "/api/receipts/receiving/act",
        json={"ids": [rid], "action": "submit"},
        headers=headers,
    )
    assert resp.status_code == 400

    # 第二层：空串穿透契约 → impl 镜像 IAE 400 "operator is required"
    resp = db_client.post(
        "/api/receipts/receiving/act",
        json={"ids": [rid], "action": "submit", "operator": ""},
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "operator is required"

    # body 整体缺省（契约 Body(None)）→ impl 400 同口径
    resp = db_client.post("/api/receipts/receiving/act", headers=headers)
    assert resp.status_code == 400

    # 两次 400 均先于 per-id 循环：receipt 完全未动
    body = _get(db_client, headers, rid)
    assert body["flowStatus"] == "receiving"
    assert body["flowHistory"] == []


@pytest.mark.fn("M03.F08.I01")
def test_act_archived_special(db_client: TestClient, bearer: str) -> None:
    """archived 特例：仅 SUBMIT 自转移 audit + reason 缺省；非 SUBMIT 拒。"""
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    cid = str(_mk_contract(db_client, headers, "C5-AR")["id"])
    rid = str(_mk_receipt(db_client, headers, "REC-AR", cid)["id"])
    _to_stage(db_client, headers, rid, "archived")

    results = _act(db_client, headers, "archived", [rid], "submit", "op-audit")
    assert results == [{"id": rid, "ok": True, "flowStatus": "archived"}]  # 自转移
    body = _get(db_client, headers, rid)
    hist: list[dict[str, object]] = body["flowHistory"]  # type: ignore[assignment]
    assert len(hist) == 7
    last = hist[-1]
    assert last["action"] == "submit" and last["from"] == "archived" and last["to"] == "archived"
    assert last["operator"] == "op-audit"
    assert last["reason"] == "archived: post-archive audit"  # 缺省 reason
    assert body["lastSubmittedBy"] == "op-audit"

    # 非 SUBMIT 拒
    results = _act(db_client, headers, "archived", [rid], "return", "op-x")
    assert results == [
        {
            "id": rid,
            "ok": False,
            "message": "Action not allowed: archived accepts only submit but got return",
        }
    ]
    results = _act(db_client, headers, "archived", [rid], "withdraw", "op-x")
    assert results == [
        {
            "id": rid,
            "ok": False,
            "message": "Action not allowed: archived accepts only submit but got withdraw",
        }
    ]

    # 非 ARCHIVED stage → stage mismatch（archived 口径）
    rid2 = str(_mk_receipt(db_client, headers, "REC-AR2", cid)["id"])
    results = _act(db_client, headers, "archived", [rid2], "submit", "op-x")
    assert results == [
        {
            "id": rid2,
            "ok": False,
            "message": "Stage mismatch: requires archived but is receiving",
        }
    ]


# ----------------------------------------------------------------------
# M03.F02.I01 任务分配
# ----------------------------------------------------------------------


@pytest.mark.fn("M03.F02.I01")
def test_assign_task_advances_receiving(db_client: TestClient, bearer: str) -> None:
    """RECEIVING 上 assign：三字段落库 + 推进 task_assignment + history operator=assigneeName。"""
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    cid = str(_mk_contract(db_client, headers, "C5-AS")["id"])
    rid = str(_mk_receipt(db_client, headers, "REC-AS", cid)["id"])

    resp = db_client.put(
        f"/api/receipts/{rid}/task",
        json={"assigneeId": "U-1", "assigneeName": "王五", "plannedTestDate": "2026-10-15"},
        headers=headers,
    )
    assert resp.status_code == _OK, resp.text
    body: dict[str, object] = resp.json()
    assert body["flowStatus"] == "task_assignment"  # 推进
    assert body["assigneeId"] == "U-1"
    assert body["assigneeName"] == "王五"
    assert body["plannedTestDate"] == "2026-10-15"
    # assignTask 直写 flowStatus+history 不走 transitionTo → lastSubmittedBy 不写（springboot 实证）
    assert "lastSubmittedBy" not in body
    hist: list[dict[str, object]] = body["flowHistory"]  # type: ignore[assignment]
    assert len(hist) == 1
    assert hist[0] == {
        "action": "submit",
        "from": "receiving",
        "to": "task_assignment",
        "operator": "王五",
        "at": hist[0]["at"],
        "reason": "M03.F02 任务分配",
    }

    # 空 payload：三字段 None 跳过、不重复推进（已非 RECEIVING）、updatedAt 恒刷
    resp = db_client.put(f"/api/receipts/{rid}/task", json={}, headers=headers)
    assert resp.status_code == _OK, resp.text
    body = resp.json()
    assert body["flowStatus"] == "task_assignment"
    assert body["assigneeName"] == "王五"  # 未提及字段不动


@pytest.mark.fn("M03.F02.I01")
def test_assign_task_no_advance_off_receiving(db_client: TestClient, bearer: str) -> None:
    """非 RECEIVING 上 assign：只刷字段不推进，history/lastSubmittedBy 不动。"""
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    cid = str(_mk_contract(db_client, headers, "C5-AN")["id"])
    rid = str(_mk_receipt(db_client, headers, "REC-AN", cid)["id"])
    _to_stage(db_client, headers, rid, "data_entry")
    before = _get(db_client, headers, rid)
    before_hist: list[dict[str, object]] = before["flowHistory"]  # type: ignore[assignment]

    resp = db_client.put(
        f"/api/receipts/{rid}/task", json={"assigneeName": "赵六"}, headers=headers
    )
    assert resp.status_code == _OK, resp.text
    body: dict[str, object] = resp.json()
    assert body["flowStatus"] == "data_entry"  # 不推进
    assert body["assigneeName"] == "赵六"
    assert body["lastSubmittedBy"] == "op-task_assignment"  # 不动
    after_hist: list[dict[str, object]] = body["flowHistory"]  # type: ignore[assignment]
    assert after_hist == before_hist  # 不写 history


# ----------------------------------------------------------------------
# M03.F09.I02 流程历史
# ----------------------------------------------------------------------


@pytest.mark.fn("M03.F09.I02")
def test_history_endpoint(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    cid = str(_mk_contract(db_client, headers, "C5-HS")["id"])
    rid = str(_mk_receipt(db_client, headers, "REC-HS", cid)["id"])

    # 空 history → []
    resp = db_client.get(f"/api/receipts/{rid}/history", headers=headers)
    assert resp.status_code == _OK, resp.text
    assert resp.json() == []

    # 一次 SUBMIT → 单条六键；reason 未传 → ""
    _act(db_client, headers, "receiving", [rid], "submit", "张三")
    resp = db_client.get(f"/api/receipts/{rid}/history", headers=headers)
    body: list[dict[str, object]] = resp.json()
    assert len(body) == 1
    entry = body[0]
    assert set(entry.keys()) == {"action", "from", "to", "operator", "at", "reason"}
    assert entry["action"] == "submit"
    assert entry["from"] == "receiving" and entry["to"] == "task_assignment"
    assert entry["operator"] == "张三"
    assert entry["reason"] == ""

    # reason 传入 → 原样
    _act(db_client, headers, "assigning", [rid], "return", "李四", reason="验收退回")
    resp = db_client.get(f"/api/receipts/{rid}/history", headers=headers)
    body = resp.json()
    assert len(body) == 2
    assert body[-1]["action"] == "return"
    assert body[-1]["reason"] == "验收退回"
    assert body[-1]["operator"] == "李四"

    # miss → 404；跨租户 → 404
    assert db_client.get("/api/receipts/R-NOPE/history", headers=headers).status_code == 404
    t2 = _switch(db_client, bearer, "TENANT-002")
    h2 = _auth(db_client, t2)
    assert db_client.get(f"/api/receipts/{rid}/history", headers=h2).status_code == 404


# ----------------------------------------------------------------------
# M03.F03.I01 检测记录
# ----------------------------------------------------------------------


@pytest.mark.fn("M03.F03.I01")
def test_records_crud(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    cid = str(_mk_contract(db_client, headers, "C5-TR")["id"])
    rid = str(_mk_receipt(db_client, headers, "REC-TR", cid)["id"])
    s1 = str(_mk_sample(db_client, headers, "S5-1", rid)["id"])
    s2 = str(_mk_sample(db_client, headers, "S5-2", rid)["id"])
    _mk_parameter(db_client, headers)

    # create：TR- 前缀 + NON_NULL 可选不落 JSON
    rec = _mk_record(db_client, headers, s1)
    assert rec["id"].startswith("TR-")
    assert rec["tenantId"] == "TENANT-001"
    assert "standardCode" not in rec
    assert "requirementCode" not in rec
    assert "verdict" not in rec

    rec_full = _mk_record(
        db_client,
        headers,
        s1,
        standardCode="STD-2",
        requirementCode="REQ-1",
        verdict="合格",
    )
    assert rec_full["standardCode"] == "STD-2"
    assert rec_full["verdict"] == "合格"

    # get + miss
    got = db_client.get(f"/api/test-records/{rec['id']}", headers=headers)
    assert got.status_code == _OK, got.text
    assert got.json()["parameterCode"] == "PAR-B5"
    assert db_client.get("/api/test-records/TR-NOPE", headers=headers).status_code == 404

    # list envelope + sampleId 过滤 + parameterCode 接受不过滤（镜像差异如实保留）
    lst = db_client.get("/api/test-records", headers=headers).json()
    assert lst["page"] == 1
    assert lst["pageSize"] == 20
    assert lst["total"] == 2
    filt = db_client.get("/api/test-records", params={"sampleId": s2}, headers=headers).json()
    assert filt["total"] == 0
    nofilter = db_client.get(
        "/api/test-records",
        params={"sampleId": s1, "parameterCode": "PAR-B5"},
        headers=headers,
    ).json()
    assert nofilter["total"] == 2  # parameterCode 不参与过滤

    # update 部分更新：六字段 None 跳过；sampleId 业务键不可改
    up = db_client.put(
        f"/api/test-records/{rec['id']}",
        json={"requirement": "≥35MPa", "result": "36.1", "sampleId": "TAMPER"},
        headers=headers,
    )
    assert up.status_code == _OK, up.text
    up_row: dict[str, object] = up.json()
    assert up_row["requirement"] == "≥35MPa"
    assert up_row["result"] == "36.1"
    assert up_row["sampleId"] == s1  # 有意遗漏镜像
    assert up_row["parameterCode"] == "PAR-B5"  # 未提及字段不动

    # verdict 改判（生成路由 PATCH /verdict，非 PUT——双侧生成 API 一致）
    vd = db_client.patch(
        f"/api/test-records/{rec['id']}/verdict", json={"verdict": "不合格"}, headers=headers
    )
    assert vd.status_code == _OK, vd.text
    assert vd.json()["verdict"] == "不合格"
    assert (
        db_client.patch(
            "/api/test-records/TR-NOPE/verdict", json={"verdict": "x"}, headers=headers
        ).status_code
        == 404
    )

    # delete 204 / 404
    assert db_client.delete(f"/api/test-records/{rec['id']}", headers=headers).status_code == 204
    assert db_client.get(f"/api/test-records/{rec['id']}", headers=headers).status_code == 404
    assert db_client.delete(f"/api/test-records/{rec['id']}", headers=headers).status_code == 404


@pytest.mark.fn("M03.F03.I01")
def test_records_tenant_isolation(db_client: TestClient, bearer: str) -> None:
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    cid = str(_mk_contract(db_client, headers, "C5-TI")["id"])
    rid = str(_mk_receipt(db_client, headers, "REC-TI", cid)["id"])
    sid = str(_mk_sample(db_client, headers, "S5-TI", rid)["id"])
    _mk_parameter(db_client, headers)
    rec = _mk_record(db_client, headers, sid)

    t2 = _switch(db_client, bearer, "TENANT-002")
    h2 = _auth(db_client, t2)
    assert db_client.get("/api/test-records", headers=h2).json()["total"] == 0
    assert db_client.get(f"/api/test-records/{rec['id']}", headers=h2).status_code == 404
    assert (
        db_client.put(
            f"/api/test-records/{rec['id']}", json={"result": "x"}, headers=h2
        ).status_code
        == 404
    )
    assert db_client.delete(f"/api/test-records/{rec['id']}", headers=h2).status_code == 404


# ----------------------------------------------------------------------
# M03.F01.I01 三态 filter submitted 分支深测（批5 流转数据实锚）
# ----------------------------------------------------------------------


@pytest.mark.fn("M03.F01.I01")
def test_receipts_filter_submitted_deep(db_client: TestClient, bearer: str) -> None:
    """submitted/not_yet 谓词锚定批4 _three_state 镜像（含 WITHDRAW 后回环节的边界）。"""
    headers = _auth(db_client, bearer)
    _mk_category(db_client, headers)
    cid = str(_mk_contract(db_client, headers, "C5-FS")["id"])
    _mk_receipt(db_client, headers, "REC-S1", cid)  # 停 receiving 不动
    s2 = str(_mk_receipt(db_client, headers, "REC-S2", cid)["id"])
    s3 = str(_mk_receipt(db_client, headers, "REC-S3", cid)["id"])
    s4 = str(_mk_receipt(db_client, headers, "REC-S4", cid)["id"])
    _act(db_client, headers, "receiving", [s2], "submit", "张三")  # S2 → task_assignment
    _act(db_client, headers, "receiving", [s3], "submit", "张三")
    _act(db_client, headers, "assigning", [s3], "submit", "李四")  # S3 → data_entry
    _act(db_client, headers, "receiving", [s4], "submit", "王五")  # S4 → task_assignment
    _act(db_client, headers, "assigning", [s4], "return", "王五")  # S4 回 receiving

    def codes(params: dict[str, object]) -> list[str]:
        resp = db_client.get("/api/receipts", params=params, headers=headers)
        assert resp.status_code == _OK, resp.text
        return [r["commissionCode"] for r in resp.json()["items"]]

    # submitted + 环节：flow_status≠环节 且 history 有 submit-from-环节
    assert codes({"filter": "submitted", "flowStatus": "receiving"}) == ["REC-S3", "REC-S2"]
    assert codes({"filter": "submitted", "flowStatus": "task_assignment"}) == ["REC-S3"]
    # submitted 无环节：history 非空 且 lastSubmittedBy 非空
    assert codes({"filter": "submitted"}) == ["REC-S4", "REC-S3", "REC-S2"]
    # not_yet + 环节：仅 flow_status==环节（无 history 条件——S4 回环节仍算 not_yet）
    assert codes({"filter": "not_yet", "flowStatus": "receiving"}) == ["REC-S4", "REC-S1"]
    # 其它值等同不传（updated_at DESC：S4 return 最后写）
    assert codes({"filter": "xx"}) == ["REC-S4", "REC-S3", "REC-S2", "REC-S1"]
