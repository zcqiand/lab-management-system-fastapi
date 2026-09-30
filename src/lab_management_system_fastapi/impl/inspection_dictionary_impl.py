"""InspectionDictionaryApiImpl —— 检测字典面 28 端点实现，语义逐条对照
lab-springboot InspectionDictionaryService / InspectionJunctionService /
InspectionDictionaryMapper（REQ-2026-003 T-2；注释标注参照方法）。

四个字典实体（specialty/object/parameter/standard）平台级（无 tenant 列，V012）；
四 junction 家族 save()=merge upsert / unlink 幂等 204。组装件（session/config）
从 RequestContext 取（组合根中间件装配）；JwtIssuer 从 app.state.jwt 取。
"""

from __future__ import annotations

from typing import Any

from lab_management_system_fastapi.apis.inspection_dictionary_api_base import (
    BaseInspectionDictionaryApi,
)
from lab_management_system_fastapi.entities import (
    InspectionObjectParameters,
    InspectionObjects,
    InspectionObjectStandards,
    InspectionParameters,
    InspectionSpecialties,
    InspectionSpecialtyObjects,
    InspectionStandardParameters,
    InspectionStandards,
)
from lab_management_system_fastapi.impl.context import get_context
from lab_management_system_fastapi.impl.inspection_support import (
    get_or_404,
    keyword_hit,
    now_iso,
    require_login,
    require_non_blank,
    unlink_junction,
    upsert_junction,
)
from lab_management_system_fastapi.models.inspection_dictionary_list_object_parameter_links200_response import (  # noqa: E501
    InspectionDictionaryListObjectParameterLinks200Response,
)
from lab_management_system_fastapi.models.inspection_dictionary_list_object_standard_links200_response import (  # noqa: E501
    InspectionDictionaryListObjectStandardLinks200Response,
)
from lab_management_system_fastapi.models.inspection_dictionary_list_objects200_response import (  # noqa: E501
    InspectionDictionaryListObjects200Response,
)
from lab_management_system_fastapi.models.inspection_dictionary_list_parameters200_response import (  # noqa: E501
    InspectionDictionaryListParameters200Response,
)
from lab_management_system_fastapi.models.inspection_dictionary_list_specialties200_response import (  # noqa: E501
    InspectionDictionaryListSpecialties200Response,
)
from lab_management_system_fastapi.models.inspection_dictionary_list_specialty_object_links200_response import (  # noqa: E501
    InspectionDictionaryListSpecialtyObjectLinks200Response,
)
from lab_management_system_fastapi.models.inspection_dictionary_list_standard_parameter_links200_response import (  # noqa: E501
    InspectionDictionaryListStandardParameterLinks200Response,
)
from lab_management_system_fastapi.models.inspection_dictionary_list_standards200_response import (  # noqa: E501
    InspectionDictionaryListStandards200Response,
)
from lab_management_system_fastapi.models.inspection_object import InspectionObject
from lab_management_system_fastapi.models.inspection_parameter import (
    InspectionParameter,
)
from lab_management_system_fastapi.models.inspection_specialty import (
    InspectionSpecialty,
)
from lab_management_system_fastapi.models.inspection_standard import (
    InspectionStandard,
)
from lab_management_system_fastapi.models.object_parameter_link import (
    ObjectParameterLink,
)
from lab_management_system_fastapi.models.object_standard_link import (
    ObjectStandardLink,
)
from lab_management_system_fastapi.models.specialty_object_link import (
    SpecialtyObjectLink,
)
from lab_management_system_fastapi.models.standard_parameter_link import (
    StandardParameterLink,
)


class InspectionDictionaryApiImpl(BaseInspectionDictionaryApi):
    """M06.F01-F04：专项/项目/参数/标准 CRUD + 四 junction 家族。"""

    # ------------------------------------------------------------------
    # 检测专项（M06.F01.I01）
    # ------------------------------------------------------------------

    async def inspection_dictionary_list_specialties(
        self, page: int | None, page_size: int | None, keyword: str | None
    ) -> InspectionDictionaryListSpecialties200Response:
        ctx = get_context()
        require_login(ctx)
        rows = [
            r
            for r in ctx.session.query(InspectionSpecialties)
            .order_by(InspectionSpecialties.sort_order, InspectionSpecialties.code)
            .all()
            if keyword_hit(keyword, r.code, r.name)
        ]
        return InspectionDictionaryListSpecialties200Response(
            items=[self._specialty_dto(r) for r in rows],
            page=page if page is not None else 1,
            pageSize=page_size if page_size is not None else len(rows),
            total=len(rows),
        )

    async def inspection_dictionary_create_specialty(self, body: Any) -> InspectionSpecialty:
        ctx = get_context()
        require_login(ctx)
        require_non_blank(code=body.code, name=body.name, official_no=body.official_no)
        now = now_iso()
        session = ctx.session
        # JPA save()=merge 镜像：同 code 再 POST = 全量覆盖（含时间戳刷新）
        row = session.get(InspectionSpecialties, (body.code,))
        if row is None:
            row = InspectionSpecialties(
                code=body.code,
                official_no=body.official_no,
                name=body.name,
                is_official=True if body.is_official is None else body.is_official,
                enabled=True if body.enabled is None else body.enabled,
                sort_order=0 if body.sort_order is None else body.sort_order,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
        else:
            row.official_no = body.official_no
            row.name = body.name
            row.is_official = True if body.is_official is None else body.is_official
            row.enabled = True if body.enabled is None else body.enabled
            row.sort_order = 0 if body.sort_order is None else body.sort_order
            row.created_at = now
            row.updated_at = now
        session.commit()
        return self._specialty_dto(row)

    async def inspection_dictionary_update_specialty(
        self, code: str, body: Any
    ) -> InspectionSpecialty:
        ctx = get_context()
        require_login(ctx)
        row = get_or_404(ctx.session, InspectionSpecialties, (code,))
        if body.official_no is not None:
            row.official_no = body.official_no
        if body.name is not None:
            row.name = body.name
        if body.is_official is not None:
            row.is_official = body.is_official
        if body.enabled is not None:
            row.enabled = body.enabled
        if body.sort_order is not None:
            row.sort_order = body.sort_order
        row.updated_at = now_iso()
        ctx.session.commit()
        return self._specialty_dto(row)

    async def inspection_dictionary_delete_specialty(self, code: str) -> None:
        ctx = get_context()
        require_login(ctx)
        row = get_or_404(ctx.session, InspectionSpecialties, (code,))
        ctx.session.delete(row)
        ctx.session.commit()

    # ------------------------------------------------------------------
    # 检测项目（M06.F02.I01）
    # ------------------------------------------------------------------

    async def inspection_dictionary_list_objects(
        self,
        page: int | None,
        page_size: int | None,
        inspection_specialty_code: str | None,
        keyword: str | None,
    ) -> InspectionDictionaryListObjects200Response:
        ctx = get_context()
        require_login(ctx)
        rows = [
            r
            for r in ctx.session.query(InspectionObjects)
            .order_by(InspectionObjects.sort_order, InspectionObjects.code)
            .all()
            if (
                inspection_specialty_code is None
                or r.inspection_specialty_code == inspection_specialty_code
            )
            and keyword_hit(keyword, r.code, r.name)
        ]
        return InspectionDictionaryListObjects200Response(
            items=[self._object_dto(r) for r in rows],
            page=page if page is not None else 1,
            pageSize=page_size if page_size is not None else len(rows),
            total=len(rows),
        )

    async def inspection_dictionary_create_object(self, body: Any) -> InspectionObject:
        ctx = get_context()
        require_login(ctx)
        require_non_blank(
            code=body.code,
            name=body.name,
            inspection_specialty_code=body.inspection_specialty_code,
        )
        now = now_iso()
        session = ctx.session
        row = session.get(InspectionObjects, (body.code,))
        if row is None:
            row = InspectionObjects(
                code=body.code,
                inspection_specialty_code=body.inspection_specialty_code,
                source_project_no=body.source_project_no,
                source_project_name=body.source_project_name,
                name=body.name,
                is_optional_for_qualification=(
                    False
                    if body.is_optional_for_qualification is None
                    else body.is_optional_for_qualification
                ),
                is_official=True if body.is_official is None else body.is_official,
                enabled=True if body.enabled is None else body.enabled,
                sort_order=0 if body.sort_order is None else body.sort_order,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
        else:
            row.inspection_specialty_code = body.inspection_specialty_code
            row.source_project_no = body.source_project_no
            row.source_project_name = body.source_project_name
            row.name = body.name
            row.is_optional_for_qualification = (
                False
                if body.is_optional_for_qualification is None
                else body.is_optional_for_qualification
            )
            row.is_official = True if body.is_official is None else body.is_official
            row.enabled = True if body.enabled is None else body.enabled
            row.sort_order = 0 if body.sort_order is None else body.sort_order
            row.created_at = now
            row.updated_at = now
        session.commit()
        return self._object_dto(row)

    async def inspection_dictionary_update_object(self, code: str, body: Any) -> InspectionObject:
        ctx = get_context()
        require_login(ctx)
        row = get_or_404(ctx.session, InspectionObjects, (code,))
        if body.inspection_specialty_code is not None:
            row.inspection_specialty_code = body.inspection_specialty_code
        if body.source_project_no is not None:
            row.source_project_no = body.source_project_no
        if body.source_project_name is not None:
            row.source_project_name = body.source_project_name
        if body.name is not None:
            row.name = body.name
        if body.is_optional_for_qualification is not None:
            row.is_optional_for_qualification = body.is_optional_for_qualification
        if body.is_official is not None:
            row.is_official = body.is_official
        if body.enabled is not None:
            row.enabled = body.enabled
        if body.sort_order is not None:
            row.sort_order = body.sort_order
        row.updated_at = now_iso()
        ctx.session.commit()
        return self._object_dto(row)

    async def inspection_dictionary_delete_object(self, code: str) -> None:
        ctx = get_context()
        require_login(ctx)
        row = get_or_404(ctx.session, InspectionObjects, (code,))
        ctx.session.delete(row)
        ctx.session.commit()

    # ------------------------------------------------------------------
    # 检测参数（M06.F03.I01）
    # ------------------------------------------------------------------

    async def inspection_dictionary_list_parameters(
        self,
        page: int | None,
        page_size: int | None,
        keyword: str | None,
        source_type: str | None,
    ) -> InspectionDictionaryListParameters200Response:
        ctx = get_context()
        require_login(ctx)
        rows = [
            r
            for r in ctx.session.query(InspectionParameters)
            .order_by(InspectionParameters.sort_order, InspectionParameters.code)
            .all()
            if (source_type is None or r.source_type == source_type)
            and keyword_hit(keyword, r.code, r.name)
        ]
        return InspectionDictionaryListParameters200Response(
            items=[self._parameter_dto(r) for r in rows],
            page=page if page is not None else 1,
            pageSize=page_size if page_size is not None else len(rows),
            total=len(rows),
        )

    async def inspection_dictionary_create_parameter(self, body: Any) -> InspectionParameter:
        ctx = get_context()
        require_login(ctx)
        require_non_blank(
            code=body.code,
            name=body.name,
            raw_name=body.raw_name,
            canonical_name=body.canonical_name,
        )
        now = now_iso()
        session = ctx.session
        row = session.get(InspectionParameters, (body.code,))
        if row is None:
            row = InspectionParameters(
                code=body.code,
                name=body.name,
                raw_name=body.raw_name,
                canonical_name=body.canonical_name,
                method_text=body.method_text,
                aliases=[] if body.aliases is None else body.aliases,
                unit=body.unit,
                source_type=("official" if body.source_type is None else body.source_type),
                sort_order=0 if body.sort_order is None else body.sort_order,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
        else:
            row.name = body.name
            row.raw_name = body.raw_name
            row.canonical_name = body.canonical_name
            row.method_text = body.method_text
            row.aliases = [] if body.aliases is None else body.aliases
            row.unit = body.unit
            row.source_type = "official" if body.source_type is None else body.source_type
            row.sort_order = 0 if body.sort_order is None else body.sort_order
            row.created_at = now
            row.updated_at = now
        session.commit()
        return self._parameter_dto(row)

    async def inspection_dictionary_update_parameter(
        self, code: str, body: Any
    ) -> InspectionParameter:
        ctx = get_context()
        require_login(ctx)
        row = get_or_404(ctx.session, InspectionParameters, (code,))
        if body.name is not None:
            row.name = body.name
        if body.raw_name is not None:
            row.raw_name = body.raw_name
        if body.canonical_name is not None:
            row.canonical_name = body.canonical_name
        if body.method_text is not None:
            row.method_text = body.method_text
        if body.aliases is not None:
            row.aliases = body.aliases
        if body.unit is not None:
            row.unit = body.unit
        if body.source_type is not None:
            row.source_type = body.source_type
        if body.sort_order is not None:
            row.sort_order = body.sort_order
        row.updated_at = now_iso()
        ctx.session.commit()
        return self._parameter_dto(row)

    async def inspection_dictionary_delete_parameter(self, code: str) -> None:
        ctx = get_context()
        require_login(ctx)
        row = get_or_404(ctx.session, InspectionParameters, (code,))
        ctx.session.delete(row)
        ctx.session.commit()

    # ------------------------------------------------------------------
    # 检测标准（M06.F04.I01）
    # ------------------------------------------------------------------

    async def inspection_dictionary_list_standards(
        self,
        page: int | None,
        page_size: int | None,
        keyword: str | None,
        status: str | None,
    ) -> InspectionDictionaryListStandards200Response:
        ctx = get_context()
        require_login(ctx)
        rows = [
            r
            for r in ctx.session.query(InspectionStandards)
            .order_by(InspectionStandards.sort_order, InspectionStandards.code)
            .all()
            if (status is None or r.status == status) and keyword_hit(keyword, r.code, r.name)
        ]
        return InspectionDictionaryListStandards200Response(
            items=[self._standard_dto(r) for r in rows],
            page=page if page is not None else 1,
            pageSize=page_size if page_size is not None else len(rows),
            total=len(rows),
        )

    async def inspection_dictionary_create_standard(self, body: Any) -> InspectionStandard:
        ctx = get_context()
        require_login(ctx)
        require_non_blank(code=body.code, name=body.name)
        now = now_iso()
        session = ctx.session
        row = session.get(InspectionStandards, (body.code,))
        if row is None:
            row = InspectionStandards(
                code=body.code,
                name=body.name,
                version=body.version,
                status="active" if body.status is None else body.status,
                source_document_id=body.source_document_id,
                source_hash=body.source_hash,
                sort_order=0 if body.sort_order is None else body.sort_order,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
        else:
            row.name = body.name
            row.version = body.version
            row.status = "active" if body.status is None else body.status
            row.source_document_id = body.source_document_id
            row.source_hash = body.source_hash
            row.sort_order = 0 if body.sort_order is None else body.sort_order
            row.created_at = now
            row.updated_at = now
        session.commit()
        return self._standard_dto(row)

    async def inspection_dictionary_update_standard(
        self, code: str, body: Any
    ) -> InspectionStandard:
        ctx = get_context()
        require_login(ctx)
        row = get_or_404(ctx.session, InspectionStandards, (code,))
        if body.name is not None:
            row.name = body.name
        if body.version is not None:
            row.version = body.version
        if body.status is not None:
            row.status = body.status
        if body.source_document_id is not None:
            row.source_document_id = body.source_document_id
        if body.source_hash is not None:
            row.source_hash = body.source_hash
        if body.sort_order is not None:
            row.sort_order = body.sort_order
        row.updated_at = now_iso()
        ctx.session.commit()
        return self._standard_dto(row)

    async def inspection_dictionary_delete_standard(self, code: str) -> None:
        ctx = get_context()
        require_login(ctx)
        row = get_or_404(ctx.session, InspectionStandards, (code,))
        ctx.session.delete(row)
        ctx.session.commit()

    # ------------------------------------------------------------------
    # junction 家族：专项↔项目（M06.F02.I02）
    # ------------------------------------------------------------------

    async def inspection_dictionary_list_specialty_object_links(
        self, inspection_specialty_code: str | None
    ) -> InspectionDictionaryListSpecialtyObjectLinks200Response:
        ctx = get_context()
        require_login(ctx)
        rows = ctx.session.query(InspectionSpecialtyObjects).all()
        if inspection_specialty_code is not None:
            rows = [r for r in rows if r.inspection_specialty_code == inspection_specialty_code]
        return InspectionDictionaryListSpecialtyObjectLinks200Response(
            items=[self._specialty_object_dto(r) for r in rows],
            page=1,
            pageSize=len(rows),
            total=len(rows),
        )

    async def inspection_dictionary_link_specialty_object(self, body: Any) -> None:
        ctx = get_context()
        require_login(ctx)
        require_non_blank(
            inspection_specialty_code=body.inspection_specialty_code,
            inspection_object_code=body.inspection_object_code,
        )
        upsert_junction(
            ctx.session,
            InspectionSpecialtyObjects,
            key_values={
                "inspection_specialty_code": body.inspection_specialty_code,
                "inspection_object_code": body.inspection_object_code,
            },
            payload_values={"remark": body.remark},
        )

    async def inspection_dictionary_unlink_specialty_object(self, body: Any) -> None:
        ctx = get_context()
        require_login(ctx)
        unlink_junction(
            ctx.session,
            InspectionSpecialtyObjects,
            key_values={
                "inspection_specialty_code": body.inspection_specialty_code,
                "inspection_object_code": body.inspection_object_code,
            },
        )

    # ------------------------------------------------------------------
    # junction 家族：项目↔参数（M06.F02.I02）
    # ------------------------------------------------------------------

    async def inspection_dictionary_list_object_parameter_links(
        self, inspection_object_code: str | None, inspection_parameter_code: str | None
    ) -> InspectionDictionaryListObjectParameterLinks200Response:
        ctx = get_context()
        require_login(ctx)
        rows = ctx.session.query(InspectionObjectParameters).all()
        if inspection_object_code is not None:
            rows = [r for r in rows if r.inspection_object_code == inspection_object_code]
        if inspection_parameter_code is not None:
            rows = [r for r in rows if r.inspection_parameter_code == inspection_parameter_code]
        return InspectionDictionaryListObjectParameterLinks200Response(
            items=[self._object_parameter_dto(r) for r in rows],
            page=1,
            pageSize=len(rows),
            total=len(rows),
        )

    async def inspection_dictionary_link_object_parameter(self, body: Any) -> None:
        ctx = get_context()
        require_login(ctx)
        require_non_blank(
            inspection_object_code=body.inspection_object_code,
            inspection_parameter_code=body.inspection_parameter_code,
        )
        # PK=(object, parameter)；qualification_level/source_page/remark 是载荷
        upsert_junction(
            ctx.session,
            InspectionObjectParameters,
            key_values={
                "inspection_object_code": body.inspection_object_code,
                "inspection_parameter_code": body.inspection_parameter_code,
            },
            payload_values={
                "qualification_level": body.qualification_level,
                "source_page": body.source_page,
                "remark": body.remark,
            },
        )

    async def inspection_dictionary_unlink_object_parameter(self, body: Any) -> None:
        ctx = get_context()
        require_login(ctx)
        unlink_junction(
            ctx.session,
            InspectionObjectParameters,
            key_values={
                "inspection_object_code": body.inspection_object_code,
                "inspection_parameter_code": body.inspection_parameter_code,
            },
        )

    # ------------------------------------------------------------------
    # junction 家族：项目↔标准（M06.F04.I02，role 是键部件）
    # ------------------------------------------------------------------

    async def inspection_dictionary_list_object_standard_links(
        self, inspection_object_code: str | None, role: str | None
    ) -> InspectionDictionaryListObjectStandardLinks200Response:
        ctx = get_context()
        require_login(ctx)
        rows = ctx.session.query(InspectionObjectStandards).all()
        if inspection_object_code is not None:
            rows = [r for r in rows if r.inspection_object_code == inspection_object_code]
        if role is not None:
            rows = [r for r in rows if r.role == role]
        return InspectionDictionaryListObjectStandardLinks200Response(
            items=[self._object_standard_dto(r) for r in rows],
            page=1,
            pageSize=len(rows),
            total=len(rows),
        )

    async def inspection_dictionary_link_object_standard(self, body: Any) -> None:
        ctx = get_context()
        require_login(ctx)
        require_non_blank(
            inspection_object_code=body.inspection_object_code,
            inspection_standard_code=body.inspection_standard_code,
            role=body.role,
        )
        upsert_junction(
            ctx.session,
            InspectionObjectStandards,
            key_values={
                "inspection_object_code": body.inspection_object_code,
                "inspection_standard_code": body.inspection_standard_code,
                "role": body.role,
            },
            payload_values={"remark": body.remark},
        )

    async def inspection_dictionary_unlink_object_standard(self, body: Any) -> None:
        ctx = get_context()
        require_login(ctx)
        unlink_junction(
            ctx.session,
            InspectionObjectStandards,
            key_values={
                "inspection_object_code": body.inspection_object_code,
                "inspection_standard_code": body.inspection_standard_code,
                "role": body.role,
            },
        )

    # ------------------------------------------------------------------
    # junction 家族：标准↔参数（M06.F03.I02，纯键家族无载荷列）
    # ------------------------------------------------------------------

    async def inspection_dictionary_list_standard_parameter_links(
        self, inspection_standard_code: str | None, inspection_parameter_code: str | None
    ) -> InspectionDictionaryListStandardParameterLinks200Response:
        ctx = get_context()
        require_login(ctx)
        rows = ctx.session.query(InspectionStandardParameters).all()
        if inspection_standard_code is not None:
            rows = [r for r in rows if r.inspection_standard_code == inspection_standard_code]
        if inspection_parameter_code is not None:
            rows = [r for r in rows if r.inspection_parameter_code == inspection_parameter_code]
        return InspectionDictionaryListStandardParameterLinks200Response(
            items=[
                StandardParameterLink(
                    inspectionStandardCode=r.inspection_standard_code,
                    inspectionParameterCode=r.inspection_parameter_code,
                )
                for r in rows
            ],
            page=1,
            pageSize=len(rows),
            total=len(rows),
        )

    async def inspection_dictionary_link_standard_parameter(self, body: Any) -> None:
        ctx = get_context()
        require_login(ctx)
        require_non_blank(
            inspection_standard_code=body.inspection_standard_code,
            inspection_parameter_code=body.inspection_parameter_code,
        )
        upsert_junction(
            ctx.session,
            InspectionStandardParameters,
            key_values={
                "inspection_standard_code": body.inspection_standard_code,
                "inspection_parameter_code": body.inspection_parameter_code,
            },
            payload_values={},
        )

    async def inspection_dictionary_unlink_standard_parameter(self, body: Any) -> None:
        ctx = get_context()
        require_login(ctx)
        unlink_junction(
            ctx.session,
            InspectionStandardParameters,
            key_values={
                "inspection_standard_code": body.inspection_standard_code,
                "inspection_parameter_code": body.inspection_parameter_code,
            },
        )

    # ------------------------------------------------------------------
    # DTO 映射（InspectionDictionaryMapper.toDto 镜像）
    # ------------------------------------------------------------------

    def _specialty_dto(self, row: Any) -> InspectionSpecialty:
        return InspectionSpecialty(
            code=row.code,
            officialNo=row.official_no,
            name=row.name,
            isOfficial=row.is_official,
            enabled=row.enabled,
            sortOrder=row.sort_order,
            createdAt=row.created_at,
            updatedAt=row.updated_at,
        )

    def _object_dto(self, row: Any) -> InspectionObject:
        return InspectionObject(
            code=row.code,
            inspectionSpecialtyCode=row.inspection_specialty_code,
            sourceProjectNo=row.source_project_no,
            sourceProjectName=row.source_project_name,
            name=row.name,
            isOptionalForQualification=row.is_optional_for_qualification,
            isOfficial=row.is_official,
            enabled=row.enabled,
            sortOrder=row.sort_order,
            createdAt=row.created_at,
            updatedAt=row.updated_at,
        )

    def _parameter_dto(self, row: Any) -> InspectionParameter:
        return InspectionParameter(
            code=row.code,
            name=row.name,
            rawName=row.raw_name,
            canonicalName=row.canonical_name,
            methodText=row.method_text,
            aliases=list(row.aliases or []),
            unit=row.unit,
            sourceType=row.source_type,
            sortOrder=row.sort_order,
            createdAt=row.created_at,
            updatedAt=row.updated_at,
        )

    def _standard_dto(self, row: Any) -> InspectionStandard:
        return InspectionStandard(
            code=row.code,
            name=row.name,
            version=row.version,
            status=row.status,
            sourceDocumentId=row.source_document_id,
            sourceHash=row.source_hash,
            sortOrder=row.sort_order,
            createdAt=row.created_at,
            updatedAt=row.updated_at,
        )

    def _specialty_object_dto(self, row: Any) -> SpecialtyObjectLink:
        return SpecialtyObjectLink(
            inspectionSpecialtyCode=row.inspection_specialty_code,
            inspectionObjectCode=row.inspection_object_code,
            remark=row.remark,
        )

    def _object_parameter_dto(self, row: Any) -> ObjectParameterLink:
        return ObjectParameterLink(
            inspectionObjectCode=row.inspection_object_code,
            inspectionParameterCode=row.inspection_parameter_code,
            qualificationLevel=row.qualification_level,
            sourcePage=row.source_page,
            remark=row.remark,
        )

    def _object_standard_dto(self, row: Any) -> ObjectStandardLink:
        return ObjectStandardLink(
            inspectionObjectCode=row.inspection_object_code,
            inspectionStandardCode=row.inspection_standard_code,
            role=row.role,
            remark=row.remark,
        )
