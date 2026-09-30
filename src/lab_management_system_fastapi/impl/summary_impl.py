"""SummaryApiImpl —— 报告汇总 + 仪表盘统计 2 端点（M05.F01，REQ-2026-007 批6），
语义对照 lab-springboot SummaryService + SampleReceiptRepository.summary native SQL
+ SummaryController。

- 鉴权：require_login + current_tenant_or_default（controller
  currentTenantIdOrDefaultStatic 镜像）。
- GET /api/summary（getReportSummary）：cat null/blank→ALL；dateFrom/dateTo null→""
  （空串=无界）；行集镜像 native SQL：tenant 等值 + (ALL=不过滤 | categoryCode 等值)
  + commission_date >=/<=（Text 字典序即日期序）+ ORDER BY commission_date DESC,
  commission_code（summary 专用排序，≠ receipts list 的 updated_at DESC）；
  renderRow 六键全 str、null→""（flowStatus/result 取 wire 值）。
- GET /api/summary/stats（getDashboardStats 全量，I03/I04 扩展段）：
  * 基础（I06）：contractCount/sampleCount=tenant 全计数（filter(tenant,"",null).size()
    镜像）；receiptCount=ALL 行数；reportCountByStatus 三桶 draft=receiving+
    task_assignment+data_entry、reviewing=review+approval、issued=issuance+archived；
    pendingTaskCount=task_assignment+data_entry+review。
  * 核心指标（I03）：todayTestCount=created_at 或 test_start_date 以服务器本地今日
    （date.today() 镜像 LocalDate.now()；created_at 存 UTC ISO——同机同行为，跨时区
    漂移双侧一致不单侧修正）；qualifiedRateByMaterial 码表全量预载（镜像 findAll——
    springboot 同款无 tenant 过滤，N+1 禁止回退）+ summaryName 关键词首命中
    （concrete=混凝土|水泥、rebar=钢筋|钢材|焊接|机械连接|连接、sand=砂|碎（卵）石|
    轻集料|颗粒级配）；pass 只计 result=="pass"；rate=Math.round 半上镜像
    （floor(x+0.5)/1000，非 Python round 银行家舍入）；reportOutputByStatus
    generated=reportCode 非空 / pending=reviewing / issued=issued。
  * 任务漏斗（I04）：funnelByStage 六段（生成模型 __properties snake_case SSOT）：
    pending_collect=receiving、received=task_assignment、testing=data_entry 且
    reportCode 空、reporting=data_entry 且 reportCode 非空、reviewing=review+
    approval、issued=issuance+archived。
"""

from __future__ import annotations

import datetime
import math
from typing import Any

from lab_management_system_fastapi.apis.summary_api_base import BaseSummaryApi
from lab_management_system_fastapi.entities import (
    Contracts,
    InspectionReportNames,
    SampleReceipts,
    Samples,
)
from lab_management_system_fastapi.impl.context import get_context
from lab_management_system_fastapi.impl.inspection_support import (
    current_tenant_or_default,
    require_login,
)
from lab_management_system_fastapi.models.dashboard_stats import DashboardStats
from lab_management_system_fastapi.models.dashboard_stats_funnel_by_stage import (
    DashboardStatsFunnelByStage,
)
from lab_management_system_fastapi.models.dashboard_stats_qualified_rate_by_material import (
    DashboardStatsQualifiedRateByMaterial,
)
from lab_management_system_fastapi.models.dashboard_stats_report_count_by_status import (
    DashboardStatsReportCountByStatus,
)
from lab_management_system_fastapi.models.dashboard_stats_report_output_by_status import (
    DashboardStatsReportOutputByStatus,
)
from lab_management_system_fastapi.models.material_qualified_rate import MaterialQualifiedRate
from lab_management_system_fastapi.models.summary_column import SummaryColumn
from lab_management_system_fastapi.models.summary_data import SummaryData

# 「ALL」特殊值 = 不按 category 过滤（SummaryService.CATEGORY_ALL 镜像）
_CATEGORY_ALL = "ALL"

_SUMMARY_COLUMNS: list[SummaryColumn] = [
    SummaryColumn(key="commissionCode", label="委托编号"),
    SummaryColumn(key="categoryCode", label="报告类别"),
    SummaryColumn(key="projectName", label="工程名称"),
    SummaryColumn(key="flowStatus", label="流程状态"),
    SummaryColumn(key="result", label="结论"),
    SummaryColumn(key="reportCode", label="报告编号"),
]

# 报告名称 summaryName → 材料类型关键词；列表序 = springboot LinkedHashMap 序（首命中）
_MATERIAL_KEYWORDS: list[tuple[str, list[str]]] = [
    ("concrete", ["混凝土", "水泥"]),
    ("rebar", ["钢筋", "钢材", "焊接", "机械连接", "连接"]),
    ("sand", ["砂", "碎（卵）石", "轻集料", "颗粒级配"]),
]


def _summary_rows(ctx: Any, tenant: str, category: str, date_from: str, date_to: str) -> list[Any]:
    """SampleReceiptRepository.summary native SQL 镜像（tenant 等值 + 类别/日期界 + 排序）。"""
    q = ctx.session.query(SampleReceipts).filter(SampleReceipts.tenant_id == tenant)
    if category != _CATEGORY_ALL:
        q = q.filter(SampleReceipts.category_code == category)
    if date_from != "":
        q = q.filter(SampleReceipts.commission_date >= date_from)
    if date_to != "":
        q = q.filter(SampleReceipts.commission_date <= date_to)
    return list(
        q.order_by(SampleReceipts.commission_date.desc(), SampleReceipts.commission_code).all()
    )


def _render_row(r: Any) -> dict[str, str]:
    """renderRow 镜像：六键全 str、null→""（LinkedHashMap 键序=列序）。"""
    return {
        "commissionCode": r.commission_code or "",
        "categoryCode": r.category_code or "",
        "projectName": r.project_name or "",
        "flowStatus": r.flow_status or "",
        "result": r.result or "",
        "reportCode": r.report_code or "",
    }


def _material_of(category_code: str | None, summary_name_by_code: dict[str, str]) -> str | None:
    """码表全量预载后内存匹配（逐条查库是 N+1，springboot 注释明令禁止回退）。"""
    if category_code is None:
        return None
    summary_name = summary_name_by_code.get(category_code, "")
    for material, keywords in _MATERIAL_KEYWORDS:
        for keyword in keywords:
            if keyword in summary_name:
                return material
    return None


def _rate(passed: int, total: int) -> float:
    """Math.round(pass/total*1000)/1000.0 半上镜像（floor(x+0.5)，非 Python 银行家）。"""
    if total <= 0:
        return 0.0
    return math.floor(passed / total * 1000 + 0.5) / 1000.0


def _mqr(
    material: str, mat_total: dict[str, int], mat_pass: dict[str, int]
) -> MaterialQualifiedRate:
    total = mat_total[material]
    passed = mat_pass[material]
    # var_pass 字段名即 `pass`（Python 关键字）→ 别名 dict 解包（populate_by_name 吃别名）
    return MaterialQualifiedRate(total=total, rate=_rate(passed, total), **{"pass": passed})


class SummaryApiImpl(BaseSummaryApi):
    """M05.F01：报告汇总 + 仪表盘统计。"""

    async def summary_get_report_summary(
        self, category_code: str | None, date_from: str | None, date_to: str | None
    ) -> SummaryData:
        ctx = get_context()
        claims = require_login(ctx)
        tenant = current_tenant_or_default(ctx, claims)
        # isBlank 镜像：null 或全空白 → ALL（空串同档）
        cat = (
            _CATEGORY_ALL if category_code is None or category_code.strip() == "" else category_code
        )
        from_ = date_from if date_from is not None else ""
        to = date_to if date_to is not None else ""
        rows = _summary_rows(ctx, tenant, cat, from_, to)
        return SummaryData(
            summaryName=f"报告汇总（{cat}）",
            columns=_SUMMARY_COLUMNS,
            rows=[_render_row(r) for r in rows],
        )

    async def summary_get_dashboard_stats(self) -> DashboardStats:
        ctx = get_context()
        claims = require_login(ctx)
        tenant = current_tenant_or_default(ctx, claims)
        receipts = _summary_rows(ctx, tenant, _CATEGORY_ALL, "", "")
        # filter(tenantId, "", null).size() 镜像 = tenant 全计数
        contract_count = ctx.session.query(Contracts).filter(Contracts.tenant_id == tenant).count()
        sample_count = ctx.session.query(Samples).filter(Samples.tenant_id == tenant).count()

        def n(*stages: str) -> int:
            return sum(1 for r in receipts if r.flow_status in stages)

        draft = n("receiving", "task_assignment", "data_entry")
        reviewing = n("review", "approval")
        issued = n("issuance", "archived")
        pending = n("task_assignment", "data_entry", "review")

        # todayTestCount：created_at 或 test_start_date 以本地今日为前缀
        today = datetime.date.today().isoformat()
        today_test_count = sum(
            1
            for r in receipts
            if (r.created_at or "").startswith(today) or (r.test_start_date or "").startswith(today)
        )

        # 码表全量预载：springboot findAll 镜像（无 tenant 过滤，同款语义）
        summary_name_by_code: dict[str, str] = {}
        for rn in ctx.session.query(InspectionReportNames).all():
            summary_name_by_code[rn.code] = rn.summary_name or ""

        mat_total: dict[str, int] = {"concrete": 0, "rebar": 0, "sand": 0}
        mat_pass: dict[str, int] = {"concrete": 0, "rebar": 0, "sand": 0}
        for r in receipts:
            material = _material_of(r.category_code, summary_name_by_code)
            if material is None:
                continue
            mat_total[material] += 1
            if r.result == "pass":
                mat_pass[material] += 1

        qualified = DashboardStatsQualifiedRateByMaterial(
            concrete=_mqr("concrete", mat_total, mat_pass),
            rebar=_mqr("rebar", mat_total, mat_pass),
            sand=_mqr("sand", mat_total, mat_pass),
        )

        report_output = DashboardStatsReportOutputByStatus(
            generated=sum(1 for r in receipts if r.report_code is not None),
            pending=reviewing,
            issued=issued,
        )
        funnel = DashboardStatsFunnelByStage(
            pending_collect=n("receiving"),
            received=n("task_assignment"),
            testing=sum(
                1 for r in receipts if r.flow_status == "data_entry" and r.report_code is None
            ),
            reporting=sum(
                1 for r in receipts if r.flow_status == "data_entry" and r.report_code is not None
            ),
            reviewing=reviewing,
            issued=issued,
        )

        return DashboardStats(
            contractCount=int(contract_count),
            receiptCount=len(receipts),
            sampleCount=int(sample_count),
            reportCountByStatus=DashboardStatsReportCountByStatus(
                draft=draft, reviewing=reviewing, issued=issued
            ),
            pendingTaskCount=pending,
            todayTestCount=today_test_count,
            qualifiedRateByMaterial=qualified,
            reportOutputByStatus=report_output,
            funnelByStage=funnel,
        )
