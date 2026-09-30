"""TestRecordsApiImpl —— 检测记录 6 端点（M03.F03.I01，REQ-2026-006 批5），
语义对照 lab-springboot TestRecordService + TestRecordMapper + TestRecordRepository
+ TestRecordController。

- tenant 收口：findByTenantIdAndId 镜像，他人租户行 miss → 404。
- list：仅 sampleId 过滤 + ORDER BY updated_at DESC, id；envelope 缺省 page=1 /
  pageSize=20（家族约定）；parameterCode 契约入参 springboot controller 接受后
  不传 service（不过滤）——镜像同款忽略（REQ-2026-006 澄清第 4 条）。
- create：id = TR-<uuid4>；契约必填校验层 400 前置；无业务前置校验（sample/
  parameter FK 撞库 500 双侧一致不特判）。
- update：applyUpdate 镜像——六字段（parameterCode/standardCode/requirementCode/
  requirement/result/verdict）None 跳过 + updatedAt=now；sample_id 不在列
  （业务键建后恒定，有意遗漏镜像）。
- verdict：只改 verdict + updatedAt（springboot controller `body == null ? null :
  body.getVerdict()` 镜像——body 整体缺省时 verdict 置 null）。
- delete：命中 → 204（组合根按 /api/test-records/ DELETE 前缀收口）。
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from lab_management_system_fastapi.apis.test_records_api_base import BaseTestRecordsApi
from lab_management_system_fastapi.entities import TestRecords
from lab_management_system_fastapi.impl.context import get_context
from lab_management_system_fastapi.impl.errors import NotFoundError
from lab_management_system_fastapi.impl.inspection_support import (
    current_tenant_or_default,
    now_iso,
    require_login,
)
from lab_management_system_fastapi.models.create_test_record_request import (
    CreateTestRecordRequest,
)
from lab_management_system_fastapi.models.test_record import TestRecord
from lab_management_system_fastapi.models.test_records_list_test_records200_response import (
    TestRecordsListTestRecords200Response,
)
from lab_management_system_fastapi.models.test_records_set_verdict_request import (
    TestRecordsSetVerdictRequest,
)
from lab_management_system_fastapi.models.update_test_record_request import (
    UpdateTestRecordRequest,
)


def _record_dto(row: Any) -> TestRecord:
    return TestRecord(
        id=row.id,
        tenantId=row.tenant_id,
        sampleId=row.sample_id,
        parameterCode=row.parameter_code,
        standardCode=row.standard_code,
        requirementCode=row.requirement_code,
        requirement=row.requirement,
        result=row.result,
        verdict=row.verdict,
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )


def _scoped_row(ctx: Any, tenant: str, id_: str) -> Any:
    """findByTenantIdAndId 镜像：他人租户行 miss → 404（隔离语义）。"""
    row = ctx.session.get(TestRecords, id_)
    if row is None or row.tenant_id != tenant:
        raise NotFoundError(f"Test record not found: {id_}")
    return row


# applyUpdate 镜像：sample_id 有意不在列（业务键建后恒定）
_UPDATE_FIELDS = (
    "parameter_code",
    "standard_code",
    "requirement_code",
    "requirement",
    "result",
    "verdict",
)


class TestRecordsApiImpl(BaseTestRecordsApi):
    """M03.F03.I01：检测记录 6 端点。"""

    async def test_records_list_test_records(
        self,
        page: int | None,
        page_size: int | None,
        sample_id: str | None,
        parameter_code: str | None,  # noqa: ARG002 — 契约入参，镜像 springboot 接受后不传 service
    ) -> TestRecordsListTestRecords200Response:
        ctx = get_context()
        claims = require_login(ctx)
        tenant = current_tenant_or_default(ctx, claims)
        rows = (
            ctx.session.query(TestRecords)
            .filter(TestRecords.tenant_id == tenant)
            .order_by(TestRecords.updated_at.desc(), TestRecords.id)
            .all()
        )
        if sample_id:
            rows = [r for r in rows if r.sample_id == sample_id]
        # parameter_code 契约入参：springboot controller 接受后不传 service，镜像不过滤
        return TestRecordsListTestRecords200Response(
            items=[_record_dto(r) for r in rows],
            page=page if page is not None else 1,
            pageSize=page_size if page_size is not None else 20,
            total=len(rows),
        )

    async def test_records_create_test_record(
        self, create_test_record_request: CreateTestRecordRequest
    ) -> TestRecord:
        ctx = get_context()
        claims = require_login(ctx)
        tenant = current_tenant_or_default(ctx, claims)
        body = create_test_record_request
        now = now_iso()
        row = TestRecords(
            id=f"TR-{uuid4()}",
            tenant_id=tenant,
            sample_id=body.sample_id,
            parameter_code=body.parameter_code,
            standard_code=body.standard_code,
            requirement_code=body.requirement_code,
            requirement=body.requirement,
            result=body.result,
            verdict=body.verdict,
            created_at=now,
            updated_at=now,
        )
        ctx.session.add(row)
        ctx.session.commit()
        ctx.session.refresh(row)
        return _record_dto(row)

    async def test_records_get_test_record(self, id: str) -> TestRecord:
        ctx = get_context()
        claims = require_login(ctx)
        row = _scoped_row(ctx, current_tenant_or_default(ctx, claims), id)
        return _record_dto(row)

    async def test_records_update_test_record(
        self, id: str, update_test_record_request: UpdateTestRecordRequest
    ) -> TestRecord:
        ctx = get_context()
        claims = require_login(ctx)
        row = _scoped_row(ctx, current_tenant_or_default(ctx, claims), id)
        body = update_test_record_request
        for name in _UPDATE_FIELDS:
            value = getattr(body, name)
            if value is not None:
                setattr(row, name, value)
        row.updated_at = now_iso()
        ctx.session.commit()
        ctx.session.refresh(row)
        return _record_dto(row)

    async def test_records_delete_test_record(self, id: str) -> None:
        ctx = get_context()
        claims = require_login(ctx)
        row = _scoped_row(ctx, current_tenant_or_default(ctx, claims), id)
        ctx.session.delete(row)
        ctx.session.commit()

    async def test_records_set_verdict(
        self, id: str, test_records_set_verdict_request: TestRecordsSetVerdictRequest
    ) -> TestRecord:
        ctx = get_context()
        claims = require_login(ctx)
        row = _scoped_row(ctx, current_tenant_or_default(ctx, claims), id)
        body = test_records_set_verdict_request
        row.verdict = None if body is None else body.verdict
        row.updated_at = now_iso()
        ctx.session.commit()
        ctx.session.refresh(row)
        return _record_dto(row)
