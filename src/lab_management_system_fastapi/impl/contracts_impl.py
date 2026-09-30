"""ContractsApiImpl —— 合同管理 5 端点（M02.F01），语义对照 lab-springboot
ContractService + ContractMapper + ContractRepository（REQ-2026-005 T-2）。

- tenant 收口：get/update/delete 按 findByTenantIdAndId 定位，他人租户行 miss → 404。
- list：keyword lower contains contract_code/project_name（n() null/"" 不过滤）+
  status 等值（JPQL `:status IS NULL OR`——None 不过滤），ORDER BY updated_at DESC,
  contract_code；envelope 缺省 page=1 / pageSize=20（springboot 控制器 T11 live 实证，
  ⚠️ 与批3 catalog 的 pageSize??size 有意不同，各自对照各自参照）。
- create：无 requireNonBlank（ContractMapper 无 IAE，契约必填走校验层 400）；
  status null → ACTIVE；id = C-<uuid4>；unique(tenant, contract_code) 撞 → 500 双侧一致
  （PK=id 与码表 PK=code 不同，跨租户同 code 可并存）。
- update：applyUpdate 镜像——部分更新 None 跳过 + updatedAt=now；contract_code 不在
  applyUpdate（业务码建后恒定，有意遗漏镜像）；无空载荷 400 特判。
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from lab_management_system_fastapi.apis.contracts_api_base import BaseContractsApi
from lab_management_system_fastapi.entities import Contracts
from lab_management_system_fastapi.impl.context import get_context
from lab_management_system_fastapi.impl.errors import NotFoundError
from lab_management_system_fastapi.impl.inspection_support import (
    current_tenant_or_default,
    now_iso,
    require_login,
)
from lab_management_system_fastapi.models.contract import Contract
from lab_management_system_fastapi.models.contract_status import ContractStatus
from lab_management_system_fastapi.models.contracts_list_contracts200_response import (
    ContractsListContracts200Response,
)


def _contract_dto(row: Any) -> Contract:
    return Contract(
        id=row.id,
        tenantId=row.tenant_id,
        contractCode=row.contract_code,
        clientUnit=row.client_unit,
        projectName=row.project_name,
        projectLocation=row.project_location,
        constructionUnit=row.construction_unit,
        inspectionSpecialtyCode=row.inspection_specialty_code,
        buildingUnit=row.building_unit,
        supervisorUnit=row.supervisor_unit,
        inspectionPerson=row.inspection_person,
        inspectionPhone=row.inspection_phone,
        witnessUnit=row.witness_unit,
        witness=row.witness,
        witnessPhone=row.witness_phone,
        contactPerson=row.contact_person,
        contactPhone=row.contact_phone,
        entrustedDate=row.entrusted_date,
        status=ContractStatus(row.status),
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )


def _scoped_row(ctx: Any, tenant: str, id_: str) -> Any:
    """findByTenantIdAndId 镜像：他人租户行 miss → 404（隔离语义）。"""
    row = ctx.session.get(Contracts, id_)
    if row is None or row.tenant_id != tenant:
        raise NotFoundError(f"Contract not found: {id_}")
    return row


# applyUpdate 镜像：contract_code 有意不在列（建后恒定）
_UPDATE_FIELDS = (
    "client_unit",
    "project_name",
    "project_location",
    "construction_unit",
    "inspection_specialty_code",
    "building_unit",
    "supervisor_unit",
    "inspection_person",
    "inspection_phone",
    "witness_unit",
    "witness",
    "witness_phone",
    "contact_person",
    "contact_phone",
    "entrusted_date",
)


class ContractsApiImpl(BaseContractsApi):
    """M02.F01：合同 CRUD（5 端点，tenant 收口）。"""

    async def contracts_list_contracts(
        self,
        page: int | None,
        page_size: int | None,
        keyword: str | None,
        status: ContractStatus | None,
    ) -> ContractsListContracts200Response:
        ctx = get_context()
        claims = require_login(ctx)
        tenant = current_tenant_or_default(ctx, claims)
        rows = (
            ctx.session.query(Contracts)
            .filter(Contracts.tenant_id == tenant)
            .order_by(Contracts.updated_at.desc(), Contracts.contract_code)
            .all()
        )
        if keyword:
            kw = keyword.lower()
            rows = [
                r
                for r in rows
                if kw in (r.contract_code or "").lower() or kw in (r.project_name or "").lower()
            ]
        if status is not None:
            rows = [r for r in rows if r.status == status.value]
        return ContractsListContracts200Response(
            items=[_contract_dto(r) for r in rows],
            page=page if page is not None else 1,
            pageSize=page_size if page_size is not None else 20,
            total=len(rows),
        )

    async def contracts_create_contract(self, create_contract_request: Any) -> Contract:
        ctx = get_context()
        claims = require_login(ctx)
        tenant = current_tenant_or_default(ctx, claims)
        body = create_contract_request
        now = now_iso()
        row = Contracts(
            id=f"C-{uuid4()}",
            tenant_id=tenant,
            contract_code=body.contract_code,
            client_unit=body.client_unit,
            project_name=body.project_name,
            project_location=body.project_location,
            construction_unit=body.construction_unit,
            inspection_specialty_code=body.inspection_specialty_code,
            building_unit=body.building_unit,
            supervisor_unit=body.supervisor_unit,
            inspection_person=body.inspection_person,
            inspection_phone=body.inspection_phone,
            witness_unit=body.witness_unit,
            witness=body.witness,
            witness_phone=body.witness_phone,
            contact_person=body.contact_person,
            contact_phone=body.contact_phone,
            entrusted_date=body.entrusted_date,
            status=body.status.value if body.status is not None else ContractStatus.ACTIVE.value,
            created_at=now,
            updated_at=now,
        )
        ctx.session.add(row)
        ctx.session.commit()
        ctx.session.refresh(row)
        return _contract_dto(row)

    async def contracts_get_contract(self, id: str) -> Contract:
        ctx = get_context()
        claims = require_login(ctx)
        row = _scoped_row(ctx, current_tenant_or_default(ctx, claims), id)
        return _contract_dto(row)

    async def contracts_update_contract(self, id: str, update_contract_request: Any) -> Contract:
        ctx = get_context()
        claims = require_login(ctx)
        row = _scoped_row(ctx, current_tenant_or_default(ctx, claims), id)
        body = update_contract_request
        for name in _UPDATE_FIELDS:
            value = getattr(body, name)
            if value is not None:
                setattr(row, name, value)
        if body.status is not None:
            row.status = body.status.value
        row.updated_at = now_iso()
        ctx.session.commit()
        ctx.session.refresh(row)
        return _contract_dto(row)

    async def contracts_delete_contract(self, id: str) -> None:
        ctx = get_context()
        claims = require_login(ctx)
        row = _scoped_row(ctx, current_tenant_or_default(ctx, claims), id)
        ctx.session.delete(row)
        ctx.session.commit()
