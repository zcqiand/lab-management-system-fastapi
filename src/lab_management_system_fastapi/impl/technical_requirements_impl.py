"""TechnicalRequirementsApiImpl —— 技术要求面 5 端点实现，语义逐条对照
lab-springboot TechnicalRequirementService（REQ-2026-003 T-3；注释标注参照方法）。

业务三键 (object, parameter, standard) 为 PG 主键；tenant_id 是普通过滤列
（springboot TechnicalRequirementKey 四部件在 PG 侧不可表达——REQ 澄清记录），
所有读写按 currentTenantIdOrDefault() 收口。缺省镜像：valueType=numeric、
judgmentMode=manual、verificationStatus=draft、sortOrder=0。comparison 契约
枚举无 springboot 缺省 'u' 成员 → 缺失裁定 400（写库会毒化后续 list 500）。
"""

from __future__ import annotations

from typing import Any

from lab_management_system_fastapi.apis.technical_requirements_api_base import (
    BaseTechnicalRequirementsApi,
)
from lab_management_system_fastapi.entities import (
    InspectionTechnicalRequirements,
)
from lab_management_system_fastapi.impl.context import get_context
from lab_management_system_fastapi.impl.errors import NotFoundError
from lab_management_system_fastapi.impl.inspection_support import (
    current_tenant_or_default,
    now_iso,
    require_login,
    require_non_blank,
)
from lab_management_system_fastapi.models.requirement_comparison import (
    RequirementComparison,
)
from lab_management_system_fastapi.models.requirement_judgment_mode import (
    RequirementJudgmentMode,
)
from lab_management_system_fastapi.models.requirement_value_type import (
    RequirementValueType,
)
from lab_management_system_fastapi.models.requirement_verification_status import (
    RequirementVerificationStatus,
)
from lab_management_system_fastapi.models.technical_requirement import (
    TechnicalRequirement,
)


def _dto(row: InspectionTechnicalRequirements) -> TechnicalRequirement:
    return TechnicalRequirement(
        tenantId=row.tenant_id,
        inspectionObjectCode=row.inspection_object_code,
        inspectionParameterCode=row.inspection_parameter_code,
        judgmentStandardCode=row.judgment_standard_code,
        conditions=row.conditions,
        valueType=RequirementValueType(row.value_type),
        minValue=row.min_value,
        maxValue=row.max_value,
        targetValue=row.target_value,
        expression=row.expression,
        unit=row.unit,
        comparison=RequirementComparison(row.comparison),
        judgmentMode=RequirementJudgmentMode(row.judgment_mode),
        verificationStatus=RequirementVerificationStatus(row.verification_status),
        clause=row.clause,
        sourcePage=row.source_page,
        sourceHash=row.source_hash,
        brand=row.brand,
        model=row.model,
        grade=row.grade,
        spec=row.spec,
        sieve=row.sieve,
        remark=row.remark,
        sortOrder=row.sort_order,
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )


class TechnicalRequirementsApiImpl(BaseTechnicalRequirementsApi):
    """M06.F06：技术要求 CRUD（三键 + tenant 收口，平台裸 List）。"""

    async def technical_requirements_list_technical_requirements(
        self,
        inspection_object_code: str | None,
        inspection_parameter_code: str | None,
        judgment_standard_code: str | None,
        verification_status: str | None,
    ) -> list[TechnicalRequirement]:
        ctx = get_context()
        claims = require_login(ctx)
        tenant = current_tenant_or_default(ctx, claims)
        rows = (
            ctx.session.query(InspectionTechnicalRequirements)
            .filter(InspectionTechnicalRequirements.tenant_id == tenant)
            .order_by(
                InspectionTechnicalRequirements.sort_order,
                InspectionTechnicalRequirements.inspection_object_code,
                InspectionTechnicalRequirements.inspection_parameter_code,
                InspectionTechnicalRequirements.judgment_standard_code,
            )
            .all()
        )
        if inspection_object_code is not None:
            rows = [r for r in rows if r.inspection_object_code == inspection_object_code]
        if inspection_parameter_code is not None:
            rows = [r for r in rows if r.inspection_parameter_code == inspection_parameter_code]
        if judgment_standard_code is not None:
            rows = [r for r in rows if r.judgment_standard_code == judgment_standard_code]
        if verification_status is not None:
            rows = [r for r in rows if r.verification_status == verification_status]
        return [_dto(r) for r in rows]

    async def technical_requirements_create_technical_requirement(
        self, create_technical_requirement_request: Any
    ) -> TechnicalRequirement:
        ctx = get_context()
        claims = require_login(ctx)
        tenant = current_tenant_or_default(ctx, claims)
        body = create_technical_requirement_request
        require_non_blank(
            inspection_object_code=body.inspection_object_code,
            inspection_parameter_code=body.inspection_parameter_code,
            judgment_standard_code=body.judgment_standard_code,
        )
        # springboot Mapper 镜像：comparison 缺失落 RequirementComparison.u。
        # wire 值是 "≥"（Java 枚举名 u/u2 是 codegen 对 ≥/≤ 的转义名——2026-10-01
        # CT live 修正：原判「'u' 在契约枚举不可表达，缺失 400」误把 Java 名当
        # wire 值；wire 值 ≥ 可表达，缺省照镜像落 ≥）。
        comparison = body.comparison if body.comparison is not None else "≥"
        session = ctx.session
        now = now_iso()
        row = session.get(
            InspectionTechnicalRequirements,
            (
                body.inspection_object_code,
                body.inspection_parameter_code,
                body.judgment_standard_code,
            ),
        )
        defaults = {
            "value_type": body.value_type or "numeric",
            "judgment_mode": body.judgment_mode or "manual",
            "verification_status": body.verification_status or "draft",
            "sort_order": body.sort_order if body.sort_order is not None else 0,
        }
        if row is None:
            row = InspectionTechnicalRequirements(
                inspection_object_code=body.inspection_object_code,
                inspection_parameter_code=body.inspection_parameter_code,
                judgment_standard_code=body.judgment_standard_code,
                tenant_id=tenant,
                conditions=body.conditions,
                min_value=body.min_value,
                max_value=body.max_value,
                target_value=body.target_value,
                expression=body.expression,
                unit=body.unit,
                comparison=comparison,
                clause=body.clause,
                source_page=body.source_page,
                source_hash=body.source_hash,
                brand=body.brand,
                model=body.model,
                grade=body.grade,
                spec=body.spec,
                sieve=body.sieve,
                remark=body.remark,
                created_at=now,
                updated_at=now,
                **defaults,
            )
            session.add(row)
        else:
            # JPA merge：同三键覆盖全部载荷字段（含 None）+ tenant 归当前
            row.tenant_id = tenant
            row.conditions = body.conditions
            row.min_value = body.min_value
            row.max_value = body.max_value
            row.target_value = body.target_value
            row.expression = body.expression
            row.unit = body.unit
            row.comparison = comparison
            row.clause = body.clause
            row.source_page = body.source_page
            row.source_hash = body.source_hash
            row.brand = body.brand
            row.model = body.model
            row.grade = body.grade
            row.spec = body.spec
            row.sieve = body.sieve
            row.remark = body.remark
            for name, value in defaults.items():
                setattr(row, name, value)
            row.updated_at = now
        session.commit()
        session.refresh(row)
        return _dto(row)

    def _scoped_row(self, ctx: Any, claims: dict[str, object], o: str, p: str, s: str) -> Any:
        """三键 + tenant 双重定位；miss（含他人租户行）→ 404（隔离语义）。"""
        tenant = current_tenant_or_default(ctx, claims)
        row = ctx.session.get(
            InspectionTechnicalRequirements,
            (o, p, s),
        )
        if row is None or row.tenant_id != tenant:
            raise NotFoundError(f"technical requirement not found: {o}/{p}/{s}")
        return row

    async def technical_requirements_get_technical_requirement(
        self,
        inspection_object_code: str,
        inspection_parameter_code: str,
        judgment_standard_code: str,
    ) -> TechnicalRequirement:
        ctx = get_context()
        claims = require_login(ctx)
        row = self._scoped_row(
            ctx, claims, inspection_object_code, inspection_parameter_code, judgment_standard_code
        )
        return _dto(row)

    async def technical_requirements_update_technical_requirement(
        self,
        inspection_object_code: str,
        inspection_parameter_code: str,
        judgment_standard_code: str,
        update_technical_requirement_request: Any,
    ) -> TechnicalRequirement:
        ctx = get_context()
        claims = require_login(ctx)
        row = self._scoped_row(
            ctx, claims, inspection_object_code, inspection_parameter_code, judgment_standard_code
        )
        body = update_technical_requirement_request
        partial = {
            name: getattr(body, name)
            for name in (
                "conditions",
                "value_type",
                "min_value",
                "max_value",
                "target_value",
                "expression",
                "unit",
                "comparison",
                "judgment_mode",
                "verification_status",
                "clause",
                "source_page",
                "source_hash",
                "brand",
                "model",
                "grade",
                "spec",
                "sieve",
                "remark",
                "sort_order",
            )
            if getattr(body, name) is not None
        }
        # 空载荷 no-op 200 镜像（springboot applyUpdate 全 null 跳过 → save 空变更）：
        # CT live 用契约外字段（requirement）做 PUT 探针，springboot Jackson 未知字段
        # 忽略 → 200；2026-10-01 修正：去掉 impl 自加的空载荷 400（springboot 无此校验）
        for name, value in partial.items():
            setattr(row, name, value)
        row.updated_at = now_iso()
        ctx.session.commit()
        ctx.session.refresh(row)
        return _dto(row)

    async def technical_requirements_delete_technical_requirement(
        self,
        inspection_object_code: str,
        inspection_parameter_code: str,
        judgment_standard_code: str,
    ) -> None:
        ctx = get_context()
        claims = require_login(ctx)
        row = self._scoped_row(
            ctx, claims, inspection_object_code, inspection_parameter_code, judgment_standard_code
        )
        ctx.session.delete(row)
        ctx.session.commit()
