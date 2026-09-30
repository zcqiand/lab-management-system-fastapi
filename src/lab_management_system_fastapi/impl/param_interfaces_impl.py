"""ParamInterfacesApiImpl —— 参数界面面 8 端点实现，语义逐条对照
lab-springboot ParamInterfaceService / InspectionJunctionService
（REQ-2026-003 T-3；注释标注参照方法）。

平台级（无 tenant 列）；save()=JPA merge 镜像；config jsonb 直转；link 行
report_name_code/config 可空载荷，unlink 幂等 204。缺省镜像：isOfficial=true、
sortOrder=0。
"""

from __future__ import annotations

from typing import Any, cast

from lab_management_system_fastapi.apis.param_interfaces_api_base import (
    BaseParamInterfacesApi,
)
from lab_management_system_fastapi.entities import (
    InspectionParamInterfaceLinks,
    InspectionParamInterfaces,
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
from lab_management_system_fastapi.models.param_interface import ParamInterface
from lab_management_system_fastapi.models.param_interface_link import (
    ParamInterfaceLink,
)
from lab_management_system_fastapi.models.param_interfaces_list_param_interface_links200_response import (  # noqa: E501
    ParamInterfacesListParamInterfaceLinks200Response,
)
from lab_management_system_fastapi.models.param_interfaces_list_param_interfaces200_response import (  # noqa: E501
    ParamInterfacesListParamInterfaces200Response,
)


def _param_interface_dto(row: InspectionParamInterfaces) -> ParamInterface:
    return ParamInterface(
        code=row.code,
        name=row.name,
        componentPath=row.component_path,
        description=row.description,
        isOfficial=row.is_official,
        sortOrder=row.sort_order,
        config=cast(dict[str, Any] | None, row.config),
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )


class ParamInterfacesApiImpl(BaseParamInterfacesApi):
    """M06.F08：参数界面 CRUD + 参数↔界面 link。"""

    # ------------------------------------------------------------------
    # 参数界面 CRUD（M06.F08.I01）
    # ------------------------------------------------------------------

    async def param_interfaces_list_param_interfaces(
        self, page: int | None, page_size: int | None, keyword: str | None
    ) -> ParamInterfacesListParamInterfaces200Response:
        ctx = get_context()
        require_login(ctx)
        rows = [
            r
            for r in ctx.session.query(InspectionParamInterfaces)
            .order_by(InspectionParamInterfaces.sort_order, InspectionParamInterfaces.code)
            .all()
            if keyword_hit(keyword, r.code, r.name or "")
        ]
        return ParamInterfacesListParamInterfaces200Response(
            items=[_param_interface_dto(r) for r in rows],
            page=page if page is not None else 1,
            pageSize=page_size if page_size is not None else len(rows),
            total=len(rows),
        )

    async def param_interfaces_create_param_interface(
        self, create_param_interface_request: Any
    ) -> ParamInterface:
        ctx = get_context()
        require_login(ctx)
        body = create_param_interface_request
        require_non_blank(code=body.code, component_path=body.component_path)
        session = ctx.session
        now = now_iso()
        row = session.get(InspectionParamInterfaces, body.code)
        if row is None:
            # 缺省镜像 springboot：isOfficial=true / sortOrder=0
            row = InspectionParamInterfaces(
                code=body.code,
                name=body.name,
                component_path=body.component_path,
                description=body.description,
                is_official=body.is_official if body.is_official is not None else True,
                sort_order=body.sort_order if body.sort_order is not None else 0,
                config=body.config,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
        else:
            # JPA merge：同主键覆盖全部载荷字段（含 None）
            row.name = body.name
            row.component_path = body.component_path
            row.description = body.description
            row.is_official = body.is_official if body.is_official is not None else True
            row.sort_order = body.sort_order if body.sort_order is not None else 0
            row.config = body.config
            row.updated_at = now
        session.commit()
        session.refresh(row)
        return _param_interface_dto(row)

    async def param_interfaces_get_param_interface(self, code: str) -> ParamInterface:
        ctx = get_context()
        require_login(ctx)
        row = ctx.session.get(InspectionParamInterfaces, code)
        if row is None:
            raise NotFoundError(f"param interface not found: {code}")
        return _param_interface_dto(row)

    async def param_interfaces_update_param_interface(
        self, code: str, update_param_interface_request: Any
    ) -> ParamInterface:
        ctx = get_context()
        require_login(ctx)
        body = update_param_interface_request
        partial = {
            name: getattr(body, name)
            for name in (
                "name",
                "component_path",
                "description",
                "is_official",
                "sort_order",
                "config",
            )
            if getattr(body, name) is not None
        }
        if not partial:
            raise BadRequestError("update payload is empty")
        row = ctx.session.get(InspectionParamInterfaces, code)
        if row is None:
            raise NotFoundError(f"param interface not found: {code}")
        for name, value in partial.items():
            setattr(row, name, value)
        row.updated_at = now_iso()
        ctx.session.commit()
        ctx.session.refresh(row)
        return _param_interface_dto(row)

    async def param_interfaces_delete_param_interface(self, code: str) -> None:
        ctx = get_context()
        require_login(ctx)
        row = ctx.session.get(InspectionParamInterfaces, code)
        if row is None:
            raise NotFoundError(f"param interface not found: {code}")
        ctx.session.delete(row)
        ctx.session.commit()

    # ------------------------------------------------------------------
    # 参数↔界面 link（M06.F08.I02）
    # ------------------------------------------------------------------

    async def param_interfaces_list_param_interface_links(
        self,
        inspection_parameter_code: str | None,
        param_interface_code: str | None,
    ) -> ParamInterfacesListParamInterfaceLinks200Response:
        ctx = get_context()
        require_login(ctx)
        rows = ctx.session.query(InspectionParamInterfaceLinks).all()
        if inspection_parameter_code is not None:
            rows = [r for r in rows if r.inspection_parameter_code == inspection_parameter_code]
        if param_interface_code is not None:
            rows = [r for r in rows if r.param_interface_code == param_interface_code]
        return ParamInterfacesListParamInterfaceLinks200Response(
            items=[
                ParamInterfaceLink(
                    inspectionParameterCode=r.inspection_parameter_code,
                    paramInterfaceCode=r.param_interface_code,
                    reportNameCode=r.report_name_code,
                    config=cast(dict[str, Any] | None, r.config),
                )
                for r in rows
            ],
            page=1,
            pageSize=len(rows),
            total=len(rows),
        )

    async def param_interfaces_link_param_interface(self, param_interface_link: Any) -> None:
        ctx = get_context()
        require_login(ctx)
        body = param_interface_link
        require_non_blank(
            inspection_parameter_code=body.inspection_parameter_code,
            param_interface_code=body.param_interface_code,
        )
        # PK=(parameter, interface)；report_name_code/config 是可空载荷（含 None 覆盖）
        upsert_junction(
            ctx.session,
            InspectionParamInterfaceLinks,
            key_values={
                "inspection_parameter_code": body.inspection_parameter_code,
                "param_interface_code": body.param_interface_code,
            },
            payload_values={
                "report_name_code": body.report_name_code,
                "config": body.config,
            },
        )

    async def param_interfaces_unlink_param_interface(
        self, param_interfaces_unlink_param_interface_request: Any
    ) -> None:
        ctx = get_context()
        require_login(ctx)
        body = param_interfaces_unlink_param_interface_request
        unlink_junction(
            ctx.session,
            InspectionParamInterfaceLinks,
            key_values={
                "inspection_parameter_code": body.inspection_parameter_code,
                "param_interface_code": body.param_interface_code,
            },
        )
