"""检测能力域共享 helper（REQ-2026-003 T-2）：语义镜像 lab-springboot 五个
Inspection*Service 的公共形状——

- nowIso()            → OffsetDateTime.now(UTC).format(ISO_OFFSET_DATE_TIME) 镜像
- require_login()     → 逐端点显式 require_bearer（生成路由无全局鉴权兜底）
- keyword_hit()       → lower(code/name) contains 镜像（None → 不过滤）
- current_tenant_or_default() → TechnicalRequirementService.currentTenantIdOrDefault 镜像
- upsert_junction()   → JPA save()=merge 镜像：同主键覆盖全部载荷字段（含 None）
- unlink_junction()   → 未命中静默 no-op（unlink 幂等，REQ-2026-001 Task 2.6）
- get_or_404()        → NoSuchElementException → 404 镜像
- require_non_blank() → requireNonBlank → 400 镜像

契约 204 无内容端点（link/unlink/delete）：impl 一律返回 None，200 null 由
组合根中间件按路径收口 204（saas 仓同款——app.py，生成区路由对若干端点只声明
了 204 responses 没声明 status_code）。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import insert as sa_insert
from sqlalchemy.orm import Session

from lab_management_system_fastapi.impl.context import RequestContext
from lab_management_system_fastapi.impl.errors import (
    BadRequestError,
    NotFoundError,
)
from lab_management_system_fastapi.impl.security import require_bearer


def now_iso() -> str:
    """springboot nowIso() 镜像：UTC ISO_OFFSET 形（+00:00 后缀，非 Z）。"""
    return datetime.now(UTC).isoformat()


def require_login(ctx: RequestContext) -> dict[str, object]:
    """逐端点显式挂 require_bearer（批1 先例：无全局兜底）。"""
    return require_bearer(ctx, ctx.request.app.state.jwt)


def keyword_hit(keyword: str | None, code: str, name: str) -> bool:
    """lower(code) contains OR lower(name) contains；keyword None/空 → 不过滤。"""
    if keyword is None:
        return True
    needle = keyword.lower()
    return needle in code.lower() or needle in name.lower()


def require_non_blank(**fields: str | None) -> None:
    """junction/link 键字段 blank 校验镜像（requireNonBlank → 400）。"""
    for name, value in fields.items():
        if value is None or not value.strip():
            raise BadRequestError(f"{name} is required")


def current_tenant_or_default(ctx: RequestContext, claims: dict[str, object]) -> str:
    """springboot TechnicalRequirementService.currentTenantIdOrDefault() 镜像：
    claim tenant_id 非空用之，否则 directory 默认租户（config 契约值，非字面量
    兜底——ADR-0019 合规）。"""
    claim = claims.get("tenant_id")
    if claim is not None and str(claim).strip():
        return str(claim)
    return ctx.config.saas_default_tenant_id


def get_or_404(session: Session, entity: type[Any], pk: tuple[Any, ...]) -> Any:
    """主键取行；miss → 404 NOT_FOUND（NoSuchElementException 镜像）。"""
    row = session.get(entity, pk)
    if row is None:
        raise NotFoundError(f"resource not found: {'/'.join(str(k) for k in pk)}")
    return row


def upsert_junction(
    session: Session,
    entity: type[Any],
    key_values: dict[str, Any],
    payload_values: dict[str, Any],
) -> None:
    """JPA save()=merge 镜像：命中主键 → 覆盖**全部载荷字段（含 None，第二次
    link 空 remark 抹掉 remark）**；未命中 → 新增行。key_values 键序必须与实体
    PrimaryKeyConstraint 列序一致（session.get 复合主键取行依赖列序）。"""
    now = now_iso()
    row = session.get(entity, tuple(key_values.values()))
    if row is None:
        session.execute(
            sa_insert(entity).values(**key_values, **payload_values, created_at=now, updated_at=now)
        )
    else:
        for name, value in payload_values.items():
            setattr(row, name, value)
        row.updated_at = now
    session.commit()


def unlink_junction(session: Session, entity: type[Any], key_values: dict[str, Any]) -> None:
    """DELETE 幂等镜像：按键删，未命中静默 no-op（200 null → 组合根收口 204）。"""
    session.query(entity).filter_by(**key_values).delete()
    session.commit()
