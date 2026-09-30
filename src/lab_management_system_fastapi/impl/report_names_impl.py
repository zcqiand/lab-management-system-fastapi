"""ReportNamesApiImpl —— 报告名称面 14 端点实现，语义逐条对照
lab-springboot InspectionReportNameService / InspectionJunctionService
（REQ-2026-003 T-3；注释标注参照方法）。

平台级（无 tenant 列）；save()=JPA merge 镜像（同主键覆盖全部载荷字段含
None）；ext_fields jsonb 直转；三 junction 家族 unlink 幂等 204，standard
家族 role 是键部件。
"""

from __future__ import annotations

from typing import Any, cast

from lab_management_system_fastapi.apis.report_names_api_base import (
    BaseReportNamesApi,
)
from lab_management_system_fastapi.entities import (
    InspectionObjectReportNames,
    InspectionReportNameParameters,
    InspectionReportNames,
    InspectionReportNameStandards,
)
from lab_management_system_fastapi.impl.context import get_context
from lab_management_system_fastapi.impl.errors import BadRequestError, NotFoundError
from lab_management_system_fastapi.impl.inspection_support import (
    keyword_hit,
    now_iso,
    require_login,
    require_non_blank,
    unlink_junction,
    upsert_junction,
)
from lab_management_system_fastapi.models.ext_field_def import ExtFieldDef
from lab_management_system_fastapi.models.inspection_report_name import (
    InspectionReportName,
)
from lab_management_system_fastapi.models.inspection_standard_role import (
    InspectionStandardRole,
)
from lab_management_system_fastapi.models.object_report_name_link import (
    ObjectReportNameLink,
)
from lab_management_system_fastapi.models.report_name_parameter_link import (
    ReportNameParameterLink,
)
from lab_management_system_fastapi.models.report_name_standard_link import (
    ReportNameStandardLink,
)
from lab_management_system_fastapi.models.report_names_list_object_report_name_links200_response import (  # noqa: E501
    ReportNamesListObjectReportNameLinks200Response,
)
from lab_management_system_fastapi.models.report_names_list_report_name_parameter_links200_response import (  # noqa: E501
    ReportNamesListReportNameParameterLinks200Response,
)
from lab_management_system_fastapi.models.report_names_list_report_name_standard_links200_response import (  # noqa: E501
    ReportNamesListReportNameStandardLinks200Response,
)
from lab_management_system_fastapi.models.report_names_list_report_names200_response import (  # noqa: E501
    ReportNamesListReportNames200Response,
)


def _ext_fields_raw(body: Any) -> list[dict[str, Any]] | None:
    """extFields 契约类型是 List[ExtFieldDef]（嵌套 pydantic 模型）——jsonb 列
    只吃纯 Python 结构，落库前 model_dump 归一化（读回由响应模型反向校验）。"""
    ext = getattr(body, "ext_fields", None)
    if ext is None:
        return None
    return [f.model_dump(by_alias=True) for f in ext]


def _report_name_dto(row: InspectionReportNames) -> InspectionReportName:
    return InspectionReportName(
        code=row.code,
        name=row.name,
        fullName=row.full_name,
        templatePath=row.template_path,
        summaryName=row.summary_name,
        extFields=cast(list[ExtFieldDef] | None, row.ext_fields),
        description=row.description,
        sortOrder=row.sort_order,
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )


class ReportNamesApiImpl(BaseReportNamesApi):
    """M06.F07：报告名称 CRUD + 三关联家族。"""

    # ------------------------------------------------------------------
    # 报告名称 CRUD（M06.F07.I01）
    # ------------------------------------------------------------------

    async def report_names_list_report_names(
        self, page: int | None, page_size: int | None, keyword: str | None
    ) -> ReportNamesListReportNames200Response:
        ctx = get_context()
        require_login(ctx)
        rows = [
            r
            for r in ctx.session.query(InspectionReportNames)
            .order_by(InspectionReportNames.sort_order, InspectionReportNames.code)
            .all()
            if keyword_hit(keyword, r.code, r.name)
        ]
        return ReportNamesListReportNames200Response(
            items=[_report_name_dto(r) for r in rows],
            page=page if page is not None else 1,
            pageSize=page_size if page_size is not None else len(rows),
            total=len(rows),
        )

    async def report_names_create_report_name(
        self, create_inspection_report_name_request: Any
    ) -> InspectionReportName:
        ctx = get_context()
        require_login(ctx)
        body = create_inspection_report_name_request
        require_non_blank(code=body.code, name=body.name)
        session = ctx.session
        now = now_iso()
        row = session.get(InspectionReportNames, body.code)
        if row is None:
            row = InspectionReportNames(
                code=body.code,
                name=body.name,
                full_name=body.full_name,
                template_path=body.template_path,
                summary_name=body.summary_name,
                ext_fields=_ext_fields_raw(body),
                description=body.description,
                sort_order=body.sort_order if body.sort_order is not None else 0,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
        else:
            # JPA merge：同主键覆盖全部载荷字段（含 None）
            row.name = body.name
            row.full_name = body.full_name
            row.template_path = body.template_path
            row.summary_name = body.summary_name
            row.ext_fields = _ext_fields_raw(body)
            row.description = body.description
            row.sort_order = body.sort_order if body.sort_order is not None else 0
            row.updated_at = now
        session.commit()
        session.refresh(row)
        return _report_name_dto(row)

    async def report_names_get_report_name(self, code: str) -> InspectionReportName:
        ctx = get_context()
        require_login(ctx)
        row = ctx.session.get(InspectionReportNames, code)
        if row is None:
            raise NotFoundError(f"report name not found: {code}")
        return _report_name_dto(row)

    async def report_names_update_report_name(
        self, code: str, update_inspection_report_name_request: Any
    ) -> InspectionReportName:
        ctx = get_context()
        require_login(ctx)
        body = update_inspection_report_name_request
        partial = {
            name: getattr(body, name)
            for name in (
                "name",
                "full_name",
                "template_path",
                "summary_name",
                "ext_fields",
                "description",
                "sort_order",
            )
            if getattr(body, name) is not None
        }
        if not partial:
            raise BadRequestError("update payload is empty")
        if "ext_fields" in partial:
            partial["ext_fields"] = _ext_fields_raw(body)
        row = ctx.session.get(InspectionReportNames, code)
        if row is None:
            raise NotFoundError(f"report name not found: {code}")
        for name, value in partial.items():
            setattr(row, name, value)
        row.updated_at = now_iso()
        ctx.session.commit()
        ctx.session.refresh(row)
        return _report_name_dto(row)

    async def report_names_delete_report_name(self, code: str) -> None:
        ctx = get_context()
        require_login(ctx)
        row = ctx.session.get(InspectionReportNames, code)
        if row is None:
            raise NotFoundError(f"report name not found: {code}")
        ctx.session.delete(row)
        ctx.session.commit()

    # ------------------------------------------------------------------
    # 三关联家族（M06.F07.I02）：save()=merge / unlink 幂等 204
    # ------------------------------------------------------------------

    @staticmethod
    def _object_link_dto(row: InspectionObjectReportNames) -> ObjectReportNameLink:
        return ObjectReportNameLink(
            inspectionObjectCode=row.inspection_object_code,
            reportNameCode=row.report_name_code,
            remark=row.remark,
        )

    @staticmethod
    def _parameter_link_dto(row: InspectionReportNameParameters) -> ReportNameParameterLink:
        return ReportNameParameterLink(
            reportNameCode=row.report_name_code,
            inspectionParameterCode=row.inspection_parameter_code,
            remark=row.remark,
        )

    @staticmethod
    def _standard_link_dto(row: InspectionReportNameStandards) -> ReportNameStandardLink:
        return ReportNameStandardLink(
            reportNameCode=row.report_name_code,
            inspectionStandardCode=row.inspection_standard_code,
            role=InspectionStandardRole(row.role),
            remark=row.remark,
        )

    async def report_names_list_object_report_name_links(
        self, inspection_object_code: str | None, report_name_code: str | None
    ) -> ReportNamesListObjectReportNameLinks200Response:
        ctx = get_context()
        require_login(ctx)
        rows = ctx.session.query(InspectionObjectReportNames).all()
        if inspection_object_code is not None:
            rows = [r for r in rows if r.inspection_object_code == inspection_object_code]
        if report_name_code is not None:
            rows = [r for r in rows if r.report_name_code == report_name_code]
        return ReportNamesListObjectReportNameLinks200Response(
            items=[self._object_link_dto(r) for r in rows],
            page=1,
            pageSize=len(rows),
            total=len(rows),
        )

    async def report_names_link_object_report_name(self, object_report_name_link: Any) -> None:
        ctx = get_context()
        require_login(ctx)
        body = object_report_name_link
        require_non_blank(
            inspection_object_code=body.inspection_object_code,
            report_name_code=body.report_name_code,
        )
        upsert_junction(
            ctx.session,
            InspectionObjectReportNames,
            key_values={
                "inspection_object_code": body.inspection_object_code,
                "report_name_code": body.report_name_code,
            },
            payload_values={"remark": body.remark},
        )

    async def report_names_unlink_object_report_name(
        self, report_names_unlink_object_report_name_request: Any
    ) -> None:
        ctx = get_context()
        require_login(ctx)
        body = report_names_unlink_object_report_name_request
        unlink_junction(
            ctx.session,
            InspectionObjectReportNames,
            key_values={
                "inspection_object_code": body.inspection_object_code,
                "report_name_code": body.report_name_code,
            },
        )

    async def report_names_list_report_name_parameter_links(
        self, report_name_code: str | None, inspection_parameter_code: str | None
    ) -> ReportNamesListReportNameParameterLinks200Response:
        ctx = get_context()
        require_login(ctx)
        rows = ctx.session.query(InspectionReportNameParameters).all()
        if report_name_code is not None:
            rows = [r for r in rows if r.report_name_code == report_name_code]
        if inspection_parameter_code is not None:
            rows = [r for r in rows if r.inspection_parameter_code == inspection_parameter_code]
        return ReportNamesListReportNameParameterLinks200Response(
            items=[self._parameter_link_dto(r) for r in rows],
            page=1,
            pageSize=len(rows),
            total=len(rows),
        )

    async def report_names_link_report_name_parameter(
        self, report_name_parameter_link: Any
    ) -> None:
        ctx = get_context()
        require_login(ctx)
        body = report_name_parameter_link
        require_non_blank(
            report_name_code=body.report_name_code,
            inspection_parameter_code=body.inspection_parameter_code,
        )
        upsert_junction(
            ctx.session,
            InspectionReportNameParameters,
            key_values={
                "report_name_code": body.report_name_code,
                "inspection_parameter_code": body.inspection_parameter_code,
            },
            payload_values={"remark": body.remark},
        )

    async def report_names_unlink_report_name_parameter(
        self, report_names_unlink_report_name_parameter_request: Any
    ) -> None:
        ctx = get_context()
        require_login(ctx)
        body = report_names_unlink_report_name_parameter_request
        unlink_junction(
            ctx.session,
            InspectionReportNameParameters,
            key_values={
                "report_name_code": body.report_name_code,
                "inspection_parameter_code": body.inspection_parameter_code,
            },
        )

    async def report_names_list_report_name_standard_links(
        self, report_name_code: str | None, role: str | None
    ) -> ReportNamesListReportNameStandardLinks200Response:
        ctx = get_context()
        require_login(ctx)
        rows = ctx.session.query(InspectionReportNameStandards).all()
        if report_name_code is not None:
            rows = [r for r in rows if r.report_name_code == report_name_code]
        if role is not None:
            rows = [r for r in rows if r.role == role]
        return ReportNamesListReportNameStandardLinks200Response(
            items=[self._standard_link_dto(r) for r in rows],
            page=1,
            pageSize=len(rows),
            total=len(rows),
        )

    async def report_names_link_report_name_standard(self, report_name_standard_link: Any) -> None:
        ctx = get_context()
        require_login(ctx)
        body = report_name_standard_link
        # role 是键部件（InspectionReportNameStandards PK 三列）
        require_non_blank(
            report_name_code=body.report_name_code,
            inspection_standard_code=body.inspection_standard_code,
            role=body.role,
        )
        upsert_junction(
            ctx.session,
            InspectionReportNameStandards,
            key_values={
                "report_name_code": body.report_name_code,
                "inspection_standard_code": body.inspection_standard_code,
                "role": body.role,
            },
            payload_values={"remark": body.remark},
        )

    async def report_names_unlink_report_name_standard(
        self, report_names_unlink_report_name_standard_request: Any
    ) -> None:
        ctx = get_context()
        require_login(ctx)
        body = report_names_unlink_report_name_standard_request
        unlink_junction(
            ctx.session,
            InspectionReportNameStandards,
            key_values={
                "report_name_code": body.report_name_code,
                "inspection_standard_code": body.inspection_standard_code,
                "role": body.role,
            },
        )
