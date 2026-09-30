"""SamplesApiImpl —— 样品 6 端点（M03.F01.I02 + M03.F09.I01 样品清单侧），语义对照
lab-springboot SampleService + SampleMapper + SampleRepository（REQ-2026-005 T-2）。

- tenant 收口：get/update/delete 按 findByTenantIdAndId 定位，他人租户行 miss → 404。
- list：receiptId 等值（n()）+ keyword lower contains sample_code/sample_name，
  ORDER BY created_at DESC, sample_code；envelope 缺省 page=1 / pageSize=20。
- create：receiptId 前置校验（tenant-scoped miss → 404 "Receipt not found"）；
  ext null → {}（fromCreate 镜像）；id = S-<uuid4>。
- update：applyUpdate 镜像——部分更新 None 跳过 + updatedAt=now；receipt_id/sample_code
  不在 applyUpdate（业务键建后恒定，有意遗漏镜像）；ext 非 None → 整体覆盖。
- updateExt（M03.F01.I07 ext 补录）：5.89 契约 ext 必填（缺省 → 校验层 400）；
  整体替换（合并是前端职责，react ReportPreviewModal 提交前已合并——springboot 注释锚定）。
- delete：samples_receipt_fk ON DELETE CASCADE（删 receipt 级联删样品，双侧 schema 一致）。
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from lab_management_system_fastapi.apis.samples_api_base import BaseSamplesApi
from lab_management_system_fastapi.entities import SampleReceipts, Samples
from lab_management_system_fastapi.impl.context import get_context
from lab_management_system_fastapi.impl.errors import NotFoundError
from lab_management_system_fastapi.impl.inspection_support import (
    current_tenant_or_default,
    now_iso,
    require_login,
)
from lab_management_system_fastapi.models.sample import Sample
from lab_management_system_fastapi.models.samples_list_samples200_response import (
    SamplesListSamples200Response,
)


def _sample_dto(row: Any) -> Sample:
    return Sample(
        id=row.id,
        tenantId=row.tenant_id,
        receiptId=row.receipt_id,
        sampleCode=row.sample_code,
        sampleName=row.sample_name,
        model=row.model,
        specification=row.specification,
        grade=row.grade,
        brand=row.brand,
        manufacturer=row.manufacturer,
        structuralPart=row.structural_part,
        representQuantity=row.represent_quantity,
        sampleQuantity=row.sample_quantity,
        batchNumber=row.batch_number,
        supplyUnit=row.supply_unit,
        arrivalDate=row.arrival_date,
        samplingDate=row.sampling_date,
        curingCondition=row.curing_condition,
        age=row.age,
        ext=row.ext if isinstance(row.ext, dict) else {},
        remark=row.remark,
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )


def _scoped_row(ctx: Any, tenant: str, id_: str) -> Any:
    """findByTenantIdAndId 镜像：他人租户行 miss → 404（隔离语义）。"""
    row = ctx.session.get(Samples, id_)
    if row is None or row.tenant_id != tenant:
        raise NotFoundError(f"Sample not found: {id_}")
    return row


# applyUpdate 镜像：receipt_id/sample_code 有意不在列（业务键建后恒定）
_UPDATE_FIELDS = (
    "sample_name",
    "model",
    "specification",
    "grade",
    "brand",
    "manufacturer",
    "structural_part",
    "represent_quantity",
    "sample_quantity",
    "batch_number",
    "supply_unit",
    "arrival_date",
    "sampling_date",
    "curing_condition",
    "age",
    "remark",
)


class SamplesApiImpl(BaseSamplesApi):
    """M03.F01.I02：样品 CRUD + ext 补录（6 端点，tenant 收口）。"""

    async def samples_list_samples(
        self,
        page: int | None,
        page_size: int | None,
        receipt_id: str | None,
        keyword: str | None,
    ) -> SamplesListSamples200Response:
        ctx = get_context()
        claims = require_login(ctx)
        tenant = current_tenant_or_default(ctx, claims)
        rows = (
            ctx.session.query(Samples)
            .filter(Samples.tenant_id == tenant)
            .order_by(Samples.created_at.desc(), Samples.sample_code)
            .all()
        )
        if receipt_id:
            rows = [r for r in rows if r.receipt_id == receipt_id]
        if keyword:
            kw = keyword.lower()
            rows = [
                r
                for r in rows
                if kw in (r.sample_code or "").lower() or kw in (r.sample_name or "").lower()
            ]
        return SamplesListSamples200Response(
            items=[_sample_dto(r) for r in rows],
            page=page if page is not None else 1,
            pageSize=page_size if page_size is not None else 20,
            total=len(rows),
        )

    async def samples_create_sample(self, create_sample_request: Any) -> Sample:
        ctx = get_context()
        claims = require_login(ctx)
        tenant = current_tenant_or_default(ctx, claims)
        body = create_sample_request
        # receipt_id 前置校验（Service create 镜像）：tenant-scoped miss → 404
        receipt = ctx.session.get(SampleReceipts, body.receipt_id)
        if receipt is None or receipt.tenant_id != tenant:
            raise NotFoundError(f"Receipt not found: {body.receipt_id}")
        now = now_iso()
        row = Samples(
            id=f"S-{uuid4()}",
            tenant_id=tenant,
            receipt_id=body.receipt_id,
            sample_code=body.sample_code,
            sample_name=body.sample_name,
            model=body.model,
            specification=body.specification,
            grade=body.grade,
            brand=body.brand,
            manufacturer=body.manufacturer,
            structural_part=body.structural_part,
            represent_quantity=body.represent_quantity,
            sample_quantity=body.sample_quantity,
            batch_number=body.batch_number,
            supply_unit=body.supply_unit,
            arrival_date=body.arrival_date,
            sampling_date=body.sampling_date,
            curing_condition=body.curing_condition,
            age=body.age,
            ext=dict(body.ext) if body.ext else {},
            remark=body.remark,
            created_at=now,
            updated_at=now,
        )
        ctx.session.add(row)
        ctx.session.commit()
        ctx.session.refresh(row)
        return _sample_dto(row)

    async def samples_get_sample(self, id: str) -> Sample:
        ctx = get_context()
        claims = require_login(ctx)
        row = _scoped_row(ctx, current_tenant_or_default(ctx, claims), id)
        return _sample_dto(row)

    async def samples_update_sample(self, id: str, update_sample_request: Any) -> Sample:
        ctx = get_context()
        claims = require_login(ctx)
        row = _scoped_row(ctx, current_tenant_or_default(ctx, claims), id)
        body = update_sample_request
        for name in _UPDATE_FIELDS:
            value = getattr(body, name)
            if value is not None:
                setattr(row, name, value)
        if body.ext is not None:
            row.ext = dict(body.ext)
        row.updated_at = now_iso()
        ctx.session.commit()
        ctx.session.refresh(row)
        return _sample_dto(row)

    async def samples_update_sample_ext(self, id: str, update_sample_ext_request: Any) -> Sample:
        ctx = get_context()
        claims = require_login(ctx)
        row = _scoped_row(ctx, current_tenant_or_default(ctx, claims), id)
        # 5.89：ext 整体替换（契约必填缺省走校验层 400，不再让构造吃 null 抛 500）
        row.ext = dict(update_sample_ext_request.ext)
        row.updated_at = now_iso()
        ctx.session.commit()
        ctx.session.refresh(row)
        return _sample_dto(row)

    async def samples_delete_sample(self, id: str) -> None:
        ctx = get_context()
        claims = require_login(ctx)
        row = _scoped_row(ctx, current_tenant_or_default(ctx, claims), id)
        ctx.session.delete(row)
        ctx.session.commit()
