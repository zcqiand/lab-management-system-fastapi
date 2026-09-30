"""批6 数据统计 red-first（REQ-2026-007）：summary 2 端点（报告汇总 + 仪表盘统计）。

镜像 lab-springboot SummaryService / SummaryController / SampleReceiptRepository.summary：
- GET /api/summary（getReportSummary）：cat null/空串→ALL；行集=tenant 等值 +
  (ALL|categoryCode 等值) + commission_date 前后缀（字符串字典序）+ ORDER BY
  commission_date DESC, commission_code；SummaryData 三键 summaryName=报告汇总（{cat}）/
  columns 6 列/rows 逐行 renderRow（六键全 str，null→""，flowStatus/result 取 wire 值）
- GET /api/summary/stats（getDashboardStats 全量）：
  - 基础（I06）：contractCount/receiptCount（=summary ALL 行数）/sampleCount（tenant 全
    计数）；reportCountByStatus 三桶 draft=receiving+task_assignment+data_entry、
    reviewing=review+approval、issued=issuance+archived；pendingTaskCount=task+entry+review
  - 核心指标（I03）：todayTestCount=created_at 或 test_start_date 以服务器本地今日为前缀
    （created_at 存 UTC ISO：00:00-08:00 本地窗口 UTC 日期≠本地日期——测试用
    baseline-delta + testStartDate 锚定，两窗口均确定）；qualifiedRateByMaterial 码表
    summaryName 关键词首命中（concrete=混凝土|水泥、rebar=钢筋|钢材|焊接|机械连接|连接、
    sand=砂|碎（卵）石|轻集料|颗粒级配），total 计全部命中单、pass 只计 result=="pass"
    （双侧无 API 写路径→恒 0，镜像不可达分支不测）、rate=round(pass/total*1000)/1000.0；
    reportOutputByStatus generated=reportCode 非空/pending=reviewing/issued=issued
  - 任务漏斗（I04）：funnelByStage 六段 snake_case 键（生成模型 __properties SSOT）：
    pending_collect=receiving、received=task_assignment、testing=data_entry 且
    reportCode 空、reporting=data_entry 且 reportCode 非空（双侧无写路径→恒 0）、
    reviewing、issued（issuance 段）
零种子依赖：数据全走 API create（FK 先建 report-names/contracts）。
"""

from __future__ import annotations

import datetime

import pytest
from fastapi.testclient import TestClient

_OK = 200

_COLUMNS = [
    "commissionCode",
    "categoryCode",
    "projectName",
    "flowStatus",
    "result",
    "reportCode",
]
_LABELS = ["委托编号", "报告类别", "工程名称", "流程状态", "结论", "报告编号"]
_CHAIN = [
    "receiving",
    "task_assignment",
    "data_entry",
    "review",
    "approval",
    "issuance",
    "archived",
]
_ACT_PATH = {
    "receiving": "receiving",
    "task_assignment": "assigning",
    "data_entry": "data-entry",
    "review": "review",
    "approval": "approve",
    "issuance": "issuance",
    "archived": "archived",
}


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


def _mk_report_name(
    db_client: TestClient, headers: dict[str, str], code: str, summary_name: str | None = None
) -> None:
    """receipt.category_code FK → inspection_report_names；summaryName 供材料关键词匹配。"""
    body: dict[str, object] = {"code": code, "name": f"{code} 名称"}
    if summary_name is not None:
        body["summaryName"] = summary_name
    resp = db_client.post("/api/report-names", json=body, headers=headers)
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
        "categoryCode": "RN-S1",
        "receivedBy": "收样员甲",
        "sampleSource": "施工现场",
        "testCategory": "混凝土",
        **extra,
    }
    resp = db_client.post("/api/receipts", json=body, headers=headers)
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
) -> list[dict[str, object]]:
    payload: dict[str, object] = {"ids": ids, "action": action, "operator": operator}
    resp = db_client.post(f"/api/receipts/{stage_path}/act", json=payload, headers=headers)
    assert resp.status_code == _OK, resp.text
    body: list[dict[str, object]] = resp.json()
    return body


def _to_stage(db_client: TestClient, headers: dict[str, str], rid: str, target: str) -> None:
    """沿 SUBMIT 链把 receipt 推到 target stage（每步 operator=op-<stage>）。"""
    i = _CHAIN.index(target)
    for stage in _CHAIN[:i]:
        _act(db_client, headers, _ACT_PATH[stage], [rid], "submit", f"op-{stage}")


def _summary(
    db_client: TestClient, headers: dict[str, str], params: dict[str, str] | None = None
) -> dict[str, object]:
    resp = db_client.get("/api/summary", params=params or {}, headers=headers)
    assert resp.status_code == _OK, resp.text
    body: dict[str, object] = resp.json()
    return body


def _stats(db_client: TestClient, headers: dict[str, str]) -> dict[str, object]:
    resp = db_client.get("/api/summary/stats", headers=headers)
    assert resp.status_code == _OK, resp.text
    body: dict[str, object] = resp.json()
    return body


def _mk_sample(
    db_client: TestClient, headers: dict[str, str], code: str, receipt_id: str, **extra: object
) -> dict[str, object]:
    body: dict[str, object] = {"receiptId": receipt_id, "sampleCode": code, **extra}
    resp = db_client.post("/api/samples", json=body, headers=headers)
    assert resp.status_code == _OK, resp.text
    row: dict[str, object] = resp.json()
    return row


# ----------------------------------------------------------------------
# M05.F01.I01 报告汇总表
# ----------------------------------------------------------------------


@pytest.mark.fn("M05.F01.I01")
def test_summary_report_table(db_client: TestClient, bearer: str) -> None:
    """列结构/排序（date DESC + code ASC）/六键 null→""/类别与日期界过滤/tenant 隔离。"""
    headers = _auth(db_client, bearer)
    _mk_report_name(db_client, headers, "RN-S1")
    _mk_report_name(db_client, headers, "RN-S2")
    cid = str(_mk_contract(db_client, headers, "C6-A")["id"])
    _mk_receipt(db_client, headers, "REC-S1", cid, commissionDate="2026-09-30")
    _mk_receipt(db_client, headers, "REC-S2", cid, commissionDate="2026-09-28")
    _mk_receipt(
        db_client, headers, "REC-S3", cid, commissionDate="2026-09-29", categoryCode="RN-S2"
    )
    _mk_receipt(db_client, headers, "REC-S0", cid, commissionDate="2026-09-30")

    body = _summary(db_client, headers)
    assert body["summaryName"] == "报告汇总（ALL）"
    assert [c["key"] for c in body["columns"]] == _COLUMNS  # type: ignore[union-attr]
    assert [c["label"] for c in body["columns"]] == _LABELS  # type: ignore[union-attr]
    rows: list[dict[str, object]] = body["rows"]  # type: ignore[assignment]
    assert [r["commissionCode"] for r in rows] == ["REC-S0", "REC-S1", "REC-S3", "REC-S2"]
    for row in rows:
        assert list(row.keys()) == _COLUMNS
        for value in row.values():
            assert isinstance(value, str)
    assert rows[0] == {
        "commissionCode": "REC-S0",
        "categoryCode": "RN-S1",
        "projectName": "",
        "flowStatus": "receiving",
        "result": "",
        "reportCode": "",
    }

    # 类别过滤：等值 + summaryName 回显类别字面（S0/S1/S2 均默认 RN-S1，S3 是 RN-S2）
    by_cat = _summary(db_client, headers, {"categoryCode": "RN-S1"})
    assert by_cat["summaryName"] == "报告汇总（RN-S1）"
    assert [r["commissionCode"] for r in by_cat["rows"]] == [  # type: ignore[union-attr]
        "REC-S0",
        "REC-S1",
        "REC-S2",
    ]

    # 日期下界 >=（含当日）、上界 <=（含当日）
    from_d = _summary(db_client, headers, {"dateFrom": "2026-09-29"})
    assert [r["commissionCode"] for r in from_d["rows"]] == ["REC-S0", "REC-S1", "REC-S3"]
    to_d = _summary(db_client, headers, {"dateTo": "2026-09-28"})
    assert [r["commissionCode"] for r in to_d["rows"]] == ["REC-S2"]
    both = _summary(db_client, headers, {"dateFrom": "2026-09-29", "dateTo": "2026-09-29"})
    assert [r["commissionCode"] for r in both["rows"]] == ["REC-S3"]

    # 空串 categoryCode → ALL（mirror：blank → ALL）
    blank = _summary(db_client, headers, {"categoryCode": ""})
    assert blank["summaryName"] == "报告汇总（ALL）"
    assert len(blank["rows"]) == 4  # type: ignore[arg-type]

    # tenant 隔离：TENANT-002 无单 → 空表（行集 tenant 等值）
    t2 = _switch(db_client, bearer, "TENANT-002")
    other = _summary(db_client, _auth(db_client, t2))
    assert other["summaryName"] == "报告汇总（ALL）"
    assert other["rows"] == []


# ----------------------------------------------------------------------
# M05.F01.I06 仪表盘基础
# ----------------------------------------------------------------------


@pytest.mark.fn("M05.F01.I06")
def test_dashboard_stats_baseline(db_client: TestClient, bearer: str) -> None:
    """零形状（空租户全计数 0 + 嵌套键恒在）+ 受控数据集的计数与三桶。"""
    headers = _auth(db_client, bearer)

    zero = _stats(db_client, headers)
    assert zero == {
        "contractCount": 0,
        "receiptCount": 0,
        "sampleCount": 0,
        "reportCountByStatus": {"draft": 0, "reviewing": 0, "issued": 0},
        "pendingTaskCount": 0,
        "todayTestCount": 0,
        "qualifiedRateByMaterial": {
            "concrete": {"total": 0, "pass": 0, "rate": 0},
            "rebar": {"total": 0, "pass": 0, "rate": 0},
            "sand": {"total": 0, "pass": 0, "rate": 0},
        },
        "reportOutputByStatus": {"generated": 0, "pending": 0, "issued": 0},
        "funnelByStage": {
            "pending_collect": 0,
            "received": 0,
            "testing": 0,
            "reporting": 0,
            "reviewing": 0,
            "issued": 0,
        },
    }

    _mk_report_name(db_client, headers, "RN-S1")
    c1 = str(_mk_contract(db_client, headers, "C6-B1")["id"])
    c2 = str(_mk_contract(db_client, headers, "C6-B2")["id"])
    r1 = str(_mk_receipt(db_client, headers, "REC-B1", c1)["id"])
    str(_mk_receipt(db_client, headers, "REC-B2", c2)["id"])
    r3 = str(_mk_receipt(db_client, headers, "REC-B3", c1)["id"])

    _act(db_client, headers, _ACT_PATH["receiving"], [r1], "submit", "op-r")
    _to_stage(db_client, headers, r3, "review")

    str(_mk_sample(db_client, headers, "SAM-B1", r1))
    str(_mk_sample(db_client, headers, "SAM-B2", r3))

    stats = _stats(db_client, headers)
    assert stats["contractCount"] == 2
    assert stats["receiptCount"] == 3
    assert stats["sampleCount"] == 2
    # draft = receiving(1: REC-B2) + task_assignment(1: REC-B1) + data_entry(0) = 2
    # reviewing = review(1) + approval(0) = 1；issued = issuance+archived = 0
    assert stats["reportCountByStatus"] == {"draft": 2, "reviewing": 1, "issued": 0}
    # pendingTaskCount = task_assignment(1) + data_entry(0) + review(1) = 2
    assert stats["pendingTaskCount"] == 2
    # todayTestCount 窗口依赖（created_at UTC vs 本地今日），不在本测试断言绝对值


# ----------------------------------------------------------------------
# M05.F01.I03 核心指标卡（todayTestCount + 材料合格率 + 报告产出）
# ----------------------------------------------------------------------


@pytest.mark.fn("M05.F01.I03")
def test_dashboard_today_and_material_rates(db_client: TestClient, bearer: str) -> None:
    """todayTestCount=created_at 或 test_start_date 本地今日前缀（baseline-delta 设计）；
    材料合格率按码表 summaryName 关键词分桶（total 全计/pass 仅 result=="pass"）。"""
    headers = _auth(db_client, bearer)
    today = datetime.date.today().isoformat()

    # 基线前建「旧日期」单：testStartDate=2020-01-01（无 today 桶贡献）
    _mk_report_name(db_client, headers, "RN-S1")
    cid = str(_mk_contract(db_client, headers, "C6-C")["id"])
    _mk_receipt(db_client, headers, "REC-C0", cid, testStartDate="2020-01-01")
    base = _stats(db_client, headers)

    # 今日单：testStartDate=本地今日 → 两窗口（UTC 日期==/≠本地日期）均 +1 确定
    _mk_receipt(db_client, headers, "REC-C1", cid, testStartDate=today)
    after = _stats(db_client, headers)
    assert after["todayTestCount"] - base["todayTestCount"] == 1

    # 材料关键词分桶：concrete=混凝土|水泥 首命中；rebar/sand 各一；未命中不入桶
    _mk_report_name(db_client, headers, "RN-M1", "混凝土试块")
    _mk_report_name(db_client, headers, "RN-M2", "普通水泥")
    _mk_report_name(db_client, headers, "RN-M3", "钢筋连接")
    _mk_report_name(db_client, headers, "RN-M4", "砂（碎、卵）石")
    _mk_report_name(db_client, headers, "RN-M5", "玻璃幕墙")
    _mk_receipt(db_client, headers, "REC-C2", cid, categoryCode="RN-M1")
    _mk_receipt(db_client, headers, "REC-C3", cid, categoryCode="RN-M2")
    _mk_receipt(db_client, headers, "REC-C4", cid, categoryCode="RN-M3")
    _mk_receipt(db_client, headers, "REC-C5", cid, categoryCode="RN-M4")
    _mk_receipt(db_client, headers, "REC-C6", cid, categoryCode="RN-M5")

    rates: dict[str, object] = _stats(db_client, headers)[  # type: ignore[assignment]
        "qualifiedRateByMaterial"
    ]
    assert rates["concrete"] == {"total": 2, "pass": 0, "rate": 0}
    assert rates["rebar"] == {"total": 1, "pass": 0, "rate": 0}
    assert rates["sand"] == {"total": 1, "pass": 0, "rate": 0}


# ----------------------------------------------------------------------
# M05.F01.I04 任务漏斗
# ----------------------------------------------------------------------


@pytest.mark.fn("M05.F01.I04")
def test_dashboard_funnel(db_client: TestClient, bearer: str) -> None:
    """funnelByStage 六段（snake_case 键）：testing/reporting 按 reportCode 有无分桶；
    同数据集交叉验证三桶与 pendingTaskCount。"""
    headers = _auth(db_client, bearer)
    _mk_report_name(db_client, headers, "RN-S1")
    cid = str(_mk_contract(db_client, headers, "C6-D")["id"])
    _mk_receipt(db_client, headers, "REC-D1", cid)  # receiving（停留）
    r2 = str(_mk_receipt(db_client, headers, "REC-D2", cid)["id"])
    r3 = str(_mk_receipt(db_client, headers, "REC-D3", cid)["id"])
    r4 = str(_mk_receipt(db_client, headers, "REC-D4", cid)["id"])
    r5 = str(_mk_receipt(db_client, headers, "REC-D5", cid)["id"])
    r6 = str(_mk_receipt(db_client, headers, "REC-D6", cid)["id"])
    _to_stage(db_client, headers, r2, "task_assignment")
    _to_stage(db_client, headers, r3, "data_entry")
    _to_stage(db_client, headers, r4, "data_entry")
    _to_stage(db_client, headers, r5, "review")
    _to_stage(db_client, headers, r6, "issuance")

    stats = _stats(db_client, headers)
    assert stats["funnelByStage"] == {
        "pending_collect": 1,
        "received": 1,
        "testing": 2,
        "reporting": 0,  # reportCode 双侧无 API 写路径 → data_entry 全落 testing
        "reviewing": 1,
        "issued": 1,
    }
    # 交叉验证：三桶 = draft(1+1+2) / reviewing(review) / issued(issuance)
    assert stats["reportCountByStatus"] == {"draft": 4, "reviewing": 1, "issued": 1}
    assert stats["pendingTaskCount"] == 1 + 2 + 1
    assert stats["reportOutputByStatus"] == {"generated": 0, "pending": 1, "issued": 1}
