"""ReceiptsApiImpl —— 接样单 CRUD 5 端点（M03.F01.I01；flow 7 + assign_task + history
留批5），语义对照 lab-springboot SampleReceiptService + SampleReceiptMapper +
SampleReceiptRepository（REQ-2026-005 T-2）。

- tenant 收口：get/update/delete 按 findByTenantIdAndId 定位，他人租户行 miss → 404。
- list：contractId 等值（n()）+ flowStatus 等值（JPQL IS NULL 判空——None 不过滤）+
  keyword lower contains commission_code/project_name，ORDER BY updated_at DESC,
  commission_code；envelope 缺省 page=1 / pageSize=20（springboot 控制器 T11 实证）。
  filter 三态（5.57 入契约，SSOT = lab-nextjs db-queries）：仅认 "not_yet"/"submitted"，
  其它值（含 null）等同不传走原路径。springboot 走 native jsonb SQL；fastapi 镜像为
  Python 侧等值判定（结果集有限无 LIMIT，语义恒等）：not_yet=指定环节停在该环节
  （无环节=history 空）；submitted=已从指定环节 submit（无环节=history 非空且
  last_submitted_by 非空）。批4 无流转数据，submitted 恒空（批5 落流转后实锚）。
- create：contractId 前置校验（tenant-scoped miss → 404 "Contract not found"）；
  flowStatus=receiving、flowHistory=[]、result=''（ReceiptResult.EMPTY）；
  id = R-<uuid4>；列表字段 null/空 → []（serializeStringList 镜像）。
- update：applyUpdate 镜像——部分更新 None 跳过 + updatedAt=now；contractId 不在
  applyUpdate（业务键建后恒定，有意遗漏镜像）；无空载荷 400 特判。
- delete：命中 → None（200 null 由组合根按 /api/receipts/ DELETE 前缀收口 204）。
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from lab_management_system_fastapi.apis.receipts_api_base import BaseReceiptsApi
from lab_management_system_fastapi.entities import Contracts, SampleReceipts
from lab_management_system_fastapi.impl.context import get_context
from lab_management_system_fastapi.impl.errors import NotFoundError
from lab_management_system_fastapi.impl.inspection_support import (
    current_tenant_or_default,
    now_iso,
    require_login,
)
from lab_management_system_fastapi.models.flow_history_entry import FlowHistoryEntry
from lab_management_system_fastapi.models.flow_status import FlowStatus
from lab_management_system_fastapi.models.receipt_result import ReceiptResult
from lab_management_system_fastapi.models.receipts_list_receipts200_response import (
    ReceiptsListReceipts200Response,
)
from lab_management_system_fastapi.models.sample_receipt import SampleReceipt


def _str_list(value: object) -> list[str]:
    """parseStringList 镜像：null/非 list → []，否则原样（toDto 恒回 list 不回 null）。"""
    if not isinstance(value, list):
        return []
    return [str(v) for v in value]


def _history(row: Any) -> list[FlowHistoryEntry]:
    """parseHistory 镜像：jsonb → List[FlowHistoryEntry]；解析失败 → []（IOException 同款）。"""
    raw = row.flow_history
    if not isinstance(raw, list):
        return []
    try:
        return [FlowHistoryEntry.model_validate(e) for e in raw]
    except Exception:
        return []


def _receipt_dto(row: Any) -> SampleReceipt:
    return SampleReceipt(
        id=row.id,
        tenantId=row.tenant_id,
        contractId=row.contract_id,
        commissionCode=row.commission_code,
        commissionDate=row.commission_date,
        commissionRegisterCode=row.commission_register_code,
        commissionRegisterDate=row.commission_register_date,
        categoryCode=row.category_code,
        projectName=row.project_name,
        clientUnit=row.client_unit,
        buildingUnit=row.building_unit,
        supervisorUnit=row.supervisor_unit,
        constructionUnit=row.construction_unit,
        witnessUnit=row.witness_unit,
        samplingLocation=row.sampling_location,
        witness=row.witness,
        witnessPhone=row.witness_phone,
        inspector=row.inspector,
        inspectorPhone=row.inspector_phone,
        receivedBy=row.received_by,
        sampleSource=row.sample_source,
        testCategory=row.test_category,
        testEnvironment=row.test_environment,
        mainEquipment=row.main_equipment,
        testOperator=row.test_operator,
        testStartDate=row.test_start_date,
        testEndDate=row.test_end_date,
        originalRecordNo=row.original_record_no,
        remark=row.remark,
        judgmentBasis=_str_list(row.judgment_basis),
        testingBasis=_str_list(row.testing_basis),
        testParameters=_str_list(row.test_parameters),
        flowStatus=FlowStatus(row.flow_status),
        flowHistory=_history(row),
        lastSubmittedBy=row.last_submitted_by,
        assigneeId=row.assignee_id,
        assigneeName=row.assignee_name,
        plannedTestDate=row.planned_test_date,
        reportCode=row.report_code,
        reportDate=row.report_date,
        conclusion=row.conclusion,
        result=ReceiptResult(row.result) if row.result is not None else None,
        issuedAt=row.issued_at.isoformat() if row.issued_at is not None else None,
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )


def _scoped_row(ctx: Any, tenant: str, id_: str) -> Any:
    """findByTenantIdAndId 镜像：他人租户行 miss → 404（隔离语义）。"""
    row = ctx.session.get(SampleReceipts, id_)
    if row is None or row.tenant_id != tenant:
        raise NotFoundError(f"Receipt not found: {id_}")
    return row


# applyUpdate 镜像：contract_id 有意不在列（业务键建后恒定）
_UPDATE_FIELDS = (
    "commission_code",
    "commission_date",
    "commission_register_code",
    "commission_register_date",
    "category_code",
    "project_name",
    "client_unit",
    "building_unit",
    "supervisor_unit",
    "construction_unit",
    "witness_unit",
    "sampling_location",
    "witness",
    "witness_phone",
    "inspector",
    "inspector_phone",
    "received_by",
    "sample_source",
    "test_category",
    "test_environment",
    "main_equipment",
    "test_operator",
    "test_start_date",
    "test_end_date",
    "original_record_no",
    "remark",
    "judgment_basis",
    "testing_basis",
    "test_parameters",
)


def _three_state(rows: list[Any], filter_value: str, stage: str) -> list[Any]:
    """filterThreeState native SQL 的 Python 侧镜像（谓词逐条对应，见模块 docstring）。"""
    out: list[Any] = []
    for r in rows:
        hist = r.flow_history if isinstance(r.flow_history, list) else []
        if filter_value == "not_yet":
            keep = (r.flow_status == stage) if stage else len(hist) == 0
        else:  # submitted
            if stage:
                keep = r.flow_status != stage and any(
                    isinstance(h, dict) and h.get("action") == "submit" and h.get("from") == stage
                    for h in hist
                )
            else:
                keep = len(hist) > 0 and r.last_submitted_by is not None
        if keep:
            out.append(r)
    return out


class ReceiptsApiImpl(BaseReceiptsApi):
    """M03.F01.I01：接样单 CRUD（本批 5 端点；flow 7 + assign_task + history 留批5）。"""

    async def receipts_list_receipts(
        self,
        page: int | None,
        page_size: int | None,
        keyword: str | None,
        contract_id: str | None,
        flow_status: FlowStatus | None,
        filter: str | None,
    ) -> ReceiptsListReceipts200Response:
        ctx = get_context()
        claims = require_login(ctx)
        tenant = current_tenant_or_default(ctx, claims)
        rows = (
            ctx.session.query(SampleReceipts)
            .filter(SampleReceipts.tenant_id == tenant)
            .order_by(SampleReceipts.updated_at.desc(), SampleReceipts.commission_code)
            .all()
        )
        if contract_id:
            rows = [r for r in rows if r.contract_id == contract_id]
        if flow_status is not None:
            rows = [r for r in rows if r.flow_status == flow_status.value]
        if keyword:
            kw = keyword.lower()
            rows = [
                r
                for r in rows
                if kw in (r.commission_code or "").lower() or kw in (r.project_name or "").lower()
            ]
        if filter in ("not_yet", "submitted"):
            stage = flow_status.value if flow_status is not None else ""
            rows = _three_state(rows, filter, stage)
        return ReceiptsListReceipts200Response(
            items=[_receipt_dto(r) for r in rows],
            page=page if page is not None else 1,
            pageSize=page_size if page_size is not None else 20,
            total=len(rows),
        )

    async def receipts_create_receipt(self, create_sample_receipt_request: Any) -> SampleReceipt:
        ctx = get_context()
        claims = require_login(ctx)
        tenant = current_tenant_or_default(ctx, claims)
        body = create_sample_receipt_request
        # contract_id 前置校验（Service create 镜像）：tenant-scoped miss → 404
        contract = ctx.session.get(Contracts, body.contract_id)
        if contract is None or contract.tenant_id != tenant:
            raise NotFoundError(f"Contract not found: {body.contract_id}")
        now = now_iso()
        row = SampleReceipts(
            id=f"R-{uuid4()}",
            tenant_id=tenant,
            contract_id=body.contract_id,
            commission_code=body.commission_code,
            commission_date=body.commission_date,
            commission_register_code=body.commission_register_code,
            commission_register_date=body.commission_register_date,
            category_code=body.category_code,
            project_name=body.project_name,
            client_unit=body.client_unit,
            building_unit=body.building_unit,
            supervisor_unit=body.supervisor_unit,
            construction_unit=body.construction_unit,
            witness_unit=body.witness_unit,
            sampling_location=body.sampling_location,
            witness=body.witness,
            witness_phone=body.witness_phone,
            inspector=body.inspector,
            inspector_phone=body.inspector_phone,
            received_by=body.received_by,
            sample_source=body.sample_source,
            test_category=body.test_category,
            test_environment=body.test_environment,
            main_equipment=body.main_equipment,
            test_operator=body.test_operator,
            test_start_date=body.test_start_date,
            test_end_date=body.test_end_date,
            original_record_no=body.original_record_no,
            remark=body.remark,
            judgment_basis=list(body.judgment_basis) if body.judgment_basis else [],
            testing_basis=list(body.testing_basis) if body.testing_basis else [],
            test_parameters=list(body.test_parameters) if body.test_parameters else [],
            flow_status=FlowStatus.RECEIVING.value,
            flow_history=[],
            result=ReceiptResult.EMPTY.value,
            created_at=now,
            updated_at=now,
        )
        ctx.session.add(row)
        ctx.session.commit()
        ctx.session.refresh(row)
        return _receipt_dto(row)

    async def receipts_get_receipt(self, id: str) -> SampleReceipt:
        ctx = get_context()
        claims = require_login(ctx)
        row = _scoped_row(ctx, current_tenant_or_default(ctx, claims), id)
        return _receipt_dto(row)

    async def receipts_update_receipt(
        self, id: str, update_sample_receipt_request: Any
    ) -> SampleReceipt:
        ctx = get_context()
        claims = require_login(ctx)
        row = _scoped_row(ctx, current_tenant_or_default(ctx, claims), id)
        body = update_sample_receipt_request
        for name in _UPDATE_FIELDS:
            value = getattr(body, name)
            if value is not None:
                setattr(row, name, value)
        row.updated_at = now_iso()
        ctx.session.commit()
        ctx.session.refresh(row)
        return _receipt_dto(row)

    async def receipts_delete_receipt(self, id: str) -> None:
        ctx = get_context()
        claims = require_login(ctx)
        row = _scoped_row(ctx, current_tenant_or_default(ctx, claims), id)
        ctx.session.delete(row)
        ctx.session.commit()
