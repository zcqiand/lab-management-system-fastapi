"""InspectionCatalogApiImpl —— 基础数据码表 16 端点实现（4 实体同构），语义逐条
对照 lab-springboot CatalogService + InspectionCatalogMapper + 各 Repository
（REQ-2026-004 T-2；注释标注参照方法）。

4 表（models=M04.F06 型号 / specs=F07 规格 / grades=F08 等级 / brands=F09 牌号）
结构一致，springboot 合并在一个 service——本 impl 同样表驱动合并（_Family）。

- tenant 收口：list 按 tenant 等值；update/delete 按 findByTenantIdAndCode 定位，
  他人租户行 miss → 404（隔离）。tenant 来源复用批2 current_tenant_or_default。
- create = JPA save() merge 镜像：手工 ID 实体 isNew=false → 撞 (tenant, code)
  全字段覆盖（含 createdAt=now，批2 字典面实体 create 同款先例）。
- update = applyUpdate 镜像：部分更新（None 跳过）+ updatedAt=now，无空载荷 400 特判。
- delete：命中 → None（200 null 由组合根按 /api/catalog/ DELETE 前缀收口 204）。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from lab_management_system_fastapi.apis.inspection_catalog_api_base import (
    BaseInspectionCatalogApi,
)
from lab_management_system_fastapi.entities import (
    InspectionBrands,
    InspectionGrades,
    InspectionModels,
    InspectionSpecs,
)
from lab_management_system_fastapi.impl.context import get_context
from lab_management_system_fastapi.impl.errors import NotFoundError
from lab_management_system_fastapi.impl.inspection_support import (
    current_tenant_or_default,
    keyword_hit,
    now_iso,
    require_login,
    require_non_blank,
)
from lab_management_system_fastapi.models.catalog_list_brands200_response import (
    CatalogListBrands200Response,
)
from lab_management_system_fastapi.models.catalog_list_grades200_response import (
    CatalogListGrades200Response,
)
from lab_management_system_fastapi.models.catalog_list_models200_response import (
    CatalogListModels200Response,
)
from lab_management_system_fastapi.models.catalog_list_specs200_response import (
    CatalogListSpecs200Response,
)
from lab_management_system_fastapi.models.inspection_brand import InspectionBrand
from lab_management_system_fastapi.models.inspection_grade import InspectionGrade
from lab_management_system_fastapi.models.inspection_model import InspectionModel
from lab_management_system_fastapi.models.inspection_spec import InspectionSpec


def _brand_dto(row: Any) -> InspectionBrand:
    return InspectionBrand(
        code=row.code,
        tenantId=row.tenant_id,
        inspectionObjectCode=row.inspection_object_code,
        name=row.name,
        remark=row.remark,
        sortOrder=row.sort_order,
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )


def _grade_dto(row: Any) -> InspectionGrade:
    return InspectionGrade(
        code=row.code,
        tenantId=row.tenant_id,
        inspectionObjectCode=row.inspection_object_code,
        name=row.name,
        remark=row.remark,
        sortOrder=row.sort_order,
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )


def _model_dto(row: Any) -> InspectionModel:
    return InspectionModel(
        code=row.code,
        tenantId=row.tenant_id,
        inspectionObjectCode=row.inspection_object_code,
        name=row.name,
        remark=row.remark,
        sortOrder=row.sort_order,
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )


def _spec_dto(row: Any) -> InspectionSpec:
    return InspectionSpec(
        code=row.code,
        tenantId=row.tenant_id,
        inspectionObjectCode=row.inspection_object_code,
        name=row.name,
        remark=row.remark,
        sortOrder=row.sort_order,
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )


@dataclass(frozen=True)
class _Family:
    """一个码表家族 = 实体 + list 响应包裹 + DTO 构造 + 404 文案标签
    （springboot NSEE message "Brand not found: code" 镜像）。"""

    entity: type[Any]
    response: type[Any]
    dto: Callable[[Any], Any]
    label: str


_BRANDS = _Family(InspectionBrands, CatalogListBrands200Response, _brand_dto, "Brand")
_GRADES = _Family(InspectionGrades, CatalogListGrades200Response, _grade_dto, "Grade")
_MODELS = _Family(InspectionModels, CatalogListModels200Response, _model_dto, "Model")
_SPECS = _Family(InspectionSpecs, CatalogListSpecs200Response, _spec_dto, "Spec")


def _list_family(
    fam: _Family,
    ctx: Any,
    claims: dict[str, object],
    page: int | None,
    page_size: int | None,
    inspection_object_code: str | None,
    keyword: str | None,
) -> Any:
    """Repository filter JPQL 镜像：tenant 等值 +（objectCode 空串/缺失不过滤）
    +（keyword 空串/缺失不过滤，非空 lower contains code/name），ORDER BY
    sort_order, code；Page 包裹 page??1 / pageSize??size / total=size，items 恒全量。"""
    tenant = current_tenant_or_default(ctx, claims)
    entity = fam.entity
    rows = (
        ctx.session.query(entity)
        .filter(entity.tenant_id == tenant)
        .order_by(entity.sort_order, entity.code)
        .all()
    )
    # n() 镜像：null→"" 恒不过滤（`'' OR 等值`）；非空等值。空串 falsy 一并覆盖。
    if inspection_object_code:
        rows = [r for r in rows if r.inspection_object_code == inspection_object_code]
    if keyword:
        rows = [r for r in rows if keyword_hit(keyword, r.code, r.name)]
    return fam.response(
        items=[fam.dto(r) for r in rows],
        page=page if page is not None else 1,
        pageSize=page_size if page_size is not None else len(rows),
        total=len(rows),
    )


def _create_family(fam: _Family, ctx: Any, claims: dict[str, object], body: Any) -> Any:
    """fromCreate 镜像 + save()=merge：撞 (tenant, code) 全字段覆盖含 createdAt。"""
    tenant = current_tenant_or_default(ctx, claims)
    require_non_blank(code=body.code, name=body.name)
    session = ctx.session
    now = now_iso()
    row = session.get(fam.entity, (body.code,))
    if row is None:
        row = fam.entity(
            code=body.code,
            tenant_id=tenant,
            inspection_object_code=body.inspection_object_code,
            name=body.name,
            remark=body.remark,
            sort_order=body.sort_order if body.sort_order is not None else 0,
            created_at=now,
            updated_at=now,
        )
        session.add(row)
    else:
        # JPA save()=merge：手工 ID 实体全字段拷贝（含 createdAt=now 刷新）
        row.tenant_id = tenant
        row.inspection_object_code = body.inspection_object_code
        row.name = body.name
        row.remark = body.remark
        row.sort_order = body.sort_order if body.sort_order is not None else 0
        row.created_at = now
        row.updated_at = now
    session.commit()
    session.refresh(row)
    return fam.dto(row)


def _scoped_row(fam: _Family, ctx: Any, claims: dict[str, object], code: str) -> Any:
    """findByTenantIdAndCode 镜像：他人租户行 miss → 404（隔离语义）。"""
    tenant = current_tenant_or_default(ctx, claims)
    row = ctx.session.get(fam.entity, (code,))
    if row is None or row.tenant_id != tenant:
        raise NotFoundError(f"{fam.label} not found: {code}")
    return row


def _update_family(fam: _Family, ctx: Any, claims: dict[str, object], code: str, body: Any) -> Any:
    """applyUpdate 镜像：部分更新（None 跳过）+ updatedAt=now；无空载荷 400 特判。"""
    require_login(ctx)
    row = _scoped_row(fam, ctx, claims, code)
    for name in ("inspection_object_code", "name", "remark", "sort_order"):
        value = getattr(body, name)
        if value is not None:
            setattr(row, name, value)
    row.updated_at = now_iso()
    ctx.session.commit()
    ctx.session.refresh(row)
    return fam.dto(row)


def _delete_family(fam: _Family, ctx: Any, claims: dict[str, object], code: str) -> None:
    """Service delete* 镜像：miss → 404；命中删除（FK RESTRICT 撞 500 双侧一致）。"""
    require_login(ctx)
    row = _scoped_row(fam, ctx, claims, code)
    ctx.session.delete(row)
    ctx.session.commit()


class InspectionCatalogApiImpl(BaseInspectionCatalogApi):
    """M04.F06-F09：码表 4 实体同构 CRUD（16 端点，tenant 收口）。"""

    # ------------------------------------------------------------------
    # M04.F09 牌号码表（brands）
    # ------------------------------------------------------------------

    async def catalog_list_brands(
        self,
        page: int | None,
        page_size: int | None,
        inspection_object_code: str | None,
        keyword: str | None,
    ) -> CatalogListBrands200Response:
        ctx = get_context()
        claims = require_login(ctx)
        return cast(
            CatalogListBrands200Response,
            _list_family(_BRANDS, ctx, claims, page, page_size, inspection_object_code, keyword),
        )

    async def catalog_create_brand(self, create_catalog_entry_request: Any) -> InspectionBrand:
        ctx = get_context()
        claims = require_login(ctx)
        return cast(
            InspectionBrand, _create_family(_BRANDS, ctx, claims, create_catalog_entry_request)
        )

    async def catalog_update_brand(
        self, code: str, update_catalog_entry_request: Any
    ) -> InspectionBrand:
        ctx = get_context()
        claims = require_login(ctx)
        return cast(
            InspectionBrand,
            _update_family(_BRANDS, ctx, claims, code, update_catalog_entry_request),
        )

    async def catalog_delete_brand(self, code: str) -> None:
        ctx = get_context()
        claims = require_login(ctx)
        _delete_family(_BRANDS, ctx, claims, code)

    # ------------------------------------------------------------------
    # M04.F08 等级码表（grades）
    # ------------------------------------------------------------------

    async def catalog_list_grades(
        self,
        page: int | None,
        page_size: int | None,
        inspection_object_code: str | None,
        keyword: str | None,
    ) -> CatalogListGrades200Response:
        ctx = get_context()
        claims = require_login(ctx)
        return cast(
            CatalogListGrades200Response,
            _list_family(_GRADES, ctx, claims, page, page_size, inspection_object_code, keyword),
        )

    async def catalog_create_grade(self, create_catalog_entry_request: Any) -> InspectionGrade:
        ctx = get_context()
        claims = require_login(ctx)
        return cast(
            InspectionGrade, _create_family(_GRADES, ctx, claims, create_catalog_entry_request)
        )

    async def catalog_update_grade(
        self, code: str, update_catalog_entry_request: Any
    ) -> InspectionGrade:
        ctx = get_context()
        claims = require_login(ctx)
        return cast(
            InspectionGrade,
            _update_family(_GRADES, ctx, claims, code, update_catalog_entry_request),
        )

    async def catalog_delete_grade(self, code: str) -> None:
        ctx = get_context()
        claims = require_login(ctx)
        _delete_family(_GRADES, ctx, claims, code)

    # ------------------------------------------------------------------
    # M04.F06 型号码表（models）
    # ------------------------------------------------------------------

    async def catalog_list_models(
        self,
        page: int | None,
        page_size: int | None,
        inspection_object_code: str | None,
        keyword: str | None,
    ) -> CatalogListModels200Response:
        ctx = get_context()
        claims = require_login(ctx)
        return cast(
            CatalogListModels200Response,
            _list_family(_MODELS, ctx, claims, page, page_size, inspection_object_code, keyword),
        )

    async def catalog_create_model(self, create_catalog_entry_request: Any) -> InspectionModel:
        ctx = get_context()
        claims = require_login(ctx)
        return cast(
            InspectionModel, _create_family(_MODELS, ctx, claims, create_catalog_entry_request)
        )

    async def catalog_update_model(
        self, code: str, update_catalog_entry_request: Any
    ) -> InspectionModel:
        ctx = get_context()
        claims = require_login(ctx)
        return cast(
            InspectionModel,
            _update_family(_MODELS, ctx, claims, code, update_catalog_entry_request),
        )

    async def catalog_delete_model(self, code: str) -> None:
        ctx = get_context()
        claims = require_login(ctx)
        _delete_family(_MODELS, ctx, claims, code)

    # ------------------------------------------------------------------
    # M04.F07 规格码表（specs）
    # ------------------------------------------------------------------

    async def catalog_list_specs(
        self,
        page: int | None,
        page_size: int | None,
        inspection_object_code: str | None,
        keyword: str | None,
    ) -> CatalogListSpecs200Response:
        ctx = get_context()
        claims = require_login(ctx)
        return cast(
            CatalogListSpecs200Response,
            _list_family(_SPECS, ctx, claims, page, page_size, inspection_object_code, keyword),
        )

    async def catalog_create_spec(self, create_catalog_entry_request: Any) -> InspectionSpec:
        ctx = get_context()
        claims = require_login(ctx)
        return cast(
            InspectionSpec, _create_family(_SPECS, ctx, claims, create_catalog_entry_request)
        )

    async def catalog_update_spec(
        self, code: str, update_catalog_entry_request: Any
    ) -> InspectionSpec:
        ctx = get_context()
        claims = require_login(ctx)
        return cast(
            InspectionSpec,
            _update_family(_SPECS, ctx, claims, code, update_catalog_entry_request),
        )

    async def catalog_delete_spec(self, code: str) -> None:
        ctx = get_context()
        claims = require_login(ctx)
        _delete_family(_SPECS, ctx, claims, code)
