"""CalculationMethodsApiImpl —— 计算方法面 5 端点实现，语义逐条对照
lab-springboot CalculationMethodService（REQ-2026-003 T-3；注释标注参照方法）。

复合主键 (inspection_object_code, inspection_parameter_code)，平台级（无
tenant 列）；save()=JPA merge 镜像（同主键覆盖全部载荷字段含 None）。
缺省镜像：algorithmType=manual、specimenCount=1、sortOrder=0。
"""

from __future__ import annotations

from typing import Any

from lab_management_system_fastapi.apis.calculation_methods_api_base import (
    BaseCalculationMethodsApi,
)
from lab_management_system_fastapi.entities import (
    InspectionCalculationMethods,
)
from lab_management_system_fastapi.impl.context import get_context
from lab_management_system_fastapi.impl.errors import BadRequestError, NotFoundError
from lab_management_system_fastapi.impl.inspection_support import (
    now_iso,
    require_login,
    require_non_blank,
)
from lab_management_system_fastapi.models.calculation_algorithm_type import (
    CalculationAlgorithmType,
)
from lab_management_system_fastapi.models.calculation_method import CalculationMethod


def _pk(body_or_obj: Any, parameter_code: Any = None) -> tuple[str, str]:
    """复合主键元组（session.get 依赖实体 PrimaryKeyConstraint 列序）。"""
    if parameter_code is None:
        return (str(body_or_obj.inspection_object_code), str(body_or_obj.inspection_parameter_code))
    return (str(body_or_obj), str(parameter_code))


def _dto(row: InspectionCalculationMethods) -> CalculationMethod:
    return CalculationMethod(
        inspectionObjectCode=row.inspection_object_code,
        inspectionParameterCode=row.inspection_parameter_code,
        testingStandardCode=row.testing_standard_code,
        reportNameCode=row.report_name_code,
        algorithmType=CalculationAlgorithmType(row.algorithm_type),
        specimenCount=row.specimen_count,
        formula=row.formula,
        conditions=row.conditions,
        roundingRule=row.rounding_rule,
        remark=row.remark,
        sortOrder=row.sort_order,
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )


class CalculationMethodsApiImpl(BaseCalculationMethodsApi):
    """M06.F05：计算方法 CRUD（复合主键，平台级裸 List）。"""

    async def calculation_methods_list_calculation_methods(
        self,
        inspection_object_code: str | None,
        inspection_parameter_code: str | None,
    ) -> list[CalculationMethod]:
        ctx = get_context()
        require_login(ctx)
        rows = (
            ctx.session.query(InspectionCalculationMethods)
            .order_by(
                InspectionCalculationMethods.sort_order,
                InspectionCalculationMethods.inspection_object_code,
                InspectionCalculationMethods.inspection_parameter_code,
            )
            .all()
        )
        if inspection_object_code is not None:
            rows = [r for r in rows if r.inspection_object_code == inspection_object_code]
        if inspection_parameter_code is not None:
            rows = [r for r in rows if r.inspection_parameter_code == inspection_parameter_code]
        return [_dto(r) for r in rows]

    async def calculation_methods_create_calculation_method(
        self, create_calculation_method_request: Any
    ) -> CalculationMethod:
        ctx = get_context()
        require_login(ctx)
        body = create_calculation_method_request
        require_non_blank(
            inspection_object_code=body.inspection_object_code,
            inspection_parameter_code=body.inspection_parameter_code,
        )
        session = ctx.session
        now = now_iso()
        pk = _pk(body)
        row = session.get(InspectionCalculationMethods, pk)
        if row is None:
            # 缺省镜像 springboot：algorithmType=manual / specimenCount=1 / sortOrder=0
            row = InspectionCalculationMethods(
                inspection_object_code=pk[0],
                inspection_parameter_code=pk[1],
                testing_standard_code=body.testing_standard_code,
                report_name_code=body.report_name_code,
                algorithm_type=body.algorithm_type or "manual",
                specimen_count=body.specimen_count if body.specimen_count is not None else 1,
                formula=body.formula,
                conditions=body.conditions,
                rounding_rule=body.rounding_rule,
                remark=body.remark,
                sort_order=body.sort_order if body.sort_order is not None else 0,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
        else:
            # JPA merge：同主键覆盖全部载荷字段（含 None）
            row.testing_standard_code = body.testing_standard_code
            row.report_name_code = body.report_name_code
            row.algorithm_type = body.algorithm_type or "manual"
            row.specimen_count = body.specimen_count if body.specimen_count is not None else 1
            row.formula = body.formula
            row.conditions = body.conditions
            row.rounding_rule = body.rounding_rule
            row.remark = body.remark
            row.sort_order = body.sort_order if body.sort_order is not None else 0
            row.updated_at = now
        session.commit()
        session.refresh(row)
        return _dto(row)

    async def calculation_methods_get_calculation_method(
        self, inspection_object_code: str, inspection_parameter_code: str
    ) -> CalculationMethod:
        ctx = get_context()
        require_login(ctx)
        row = ctx.session.get(
            InspectionCalculationMethods,
            (inspection_object_code, inspection_parameter_code),
        )
        if row is None:
            raise NotFoundError(
                f"calculation method not found: "
                f"{inspection_object_code}/{inspection_parameter_code}"
            )
        return _dto(row)

    async def calculation_methods_update_calculation_method(
        self,
        inspection_object_code: str,
        inspection_parameter_code: str,
        update_calculation_method_request: Any,
    ) -> CalculationMethod:
        ctx = get_context()
        require_login(ctx)
        body = update_calculation_method_request
        if (
            body.testing_standard_code is None
            and body.report_name_code is None
            and body.algorithm_type is None
            and body.specimen_count is None
            and body.formula is None
            and body.conditions is None
            and body.rounding_rule is None
            and body.remark is None
            and body.sort_order is None
        ):
            raise BadRequestError("update payload is empty")
        session = ctx.session
        row = session.get(
            InspectionCalculationMethods,
            (inspection_object_code, inspection_parameter_code),
        )
        if row is None:
            raise NotFoundError(
                f"calculation method not found: "
                f"{inspection_object_code}/{inspection_parameter_code}"
            )
        for name in (
            "testing_standard_code",
            "report_name_code",
            "algorithm_type",
            "specimen_count",
            "formula",
            "conditions",
            "rounding_rule",
            "remark",
            "sort_order",
        ):
            value = getattr(body, name)
            if value is not None:
                setattr(row, name, value)
        row.updated_at = now_iso()
        session.commit()
        session.refresh(row)
        return _dto(row)

    async def calculation_methods_delete_calculation_method(
        self, inspection_object_code: str, inspection_parameter_code: str
    ) -> None:
        ctx = get_context()
        require_login(ctx)
        session = ctx.session
        row = session.get(
            InspectionCalculationMethods,
            (inspection_object_code, inspection_parameter_code),
        )
        if row is None:
            raise NotFoundError(
                f"calculation method not found: "
                f"{inspection_object_code}/{inspection_parameter_code}"
            )
        session.delete(row)
        session.commit()
