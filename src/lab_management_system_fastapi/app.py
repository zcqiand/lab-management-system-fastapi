"""组合根 —— 手写（生成器 main.py 的手写替代，禁改生成区）。

create_app(config, engine) 工厂装配（镜像 saas-identity-platform-fastapi 同名模块，
REQ-2026-002 T-4）：生成 router + 每请求上下文中间件 + 家族错误契约 handler +
CORS 白名单（lab.cors.allowed-origins 镜像 springboot SecurityConfig）。
模块级 ``app``（uvicorn 入口 ``lab_management_system_fastapi.app:app``）经 PEP 562
惰性构建：首次访问才读 env fail-fast —— import 期不读 env，CI 装配冒烟与 pytest
收集不需要真实环境。
"""

from __future__ import annotations

import inspect
import types
from collections.abc import Awaitable, Callable
from typing import Union, get_args, get_origin

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import Strict
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from starlette.datastructures import State

from lab_management_system_fastapi.apis.auth_api import router as auth_api_router
from lab_management_system_fastapi.apis.calculation_methods_api import (
    router as calculation_methods_api_router,
)
from lab_management_system_fastapi.apis.contracts_api import router as contracts_api_router
from lab_management_system_fastapi.apis.frontend_bind_meta_api import (
    router as frontend_bind_meta_api_router,
)
from lab_management_system_fastapi.apis.inspection_catalog_api import (
    router as inspection_catalog_api_router,
)
from lab_management_system_fastapi.apis.inspection_dictionary_api import (
    router as inspection_dictionary_api_router,
)
from lab_management_system_fastapi.apis.param_interfaces_api import (
    router as param_interfaces_api_router,
)
from lab_management_system_fastapi.apis.receipts_api import router as receipts_api_router
from lab_management_system_fastapi.apis.report_names_api import router as report_names_api_router
from lab_management_system_fastapi.apis.samples_api import router as samples_api_router
from lab_management_system_fastapi.apis.summary_api import router as summary_api_router
from lab_management_system_fastapi.apis.technical_requirements_api import (
    router as technical_requirements_api_router,
)
from lab_management_system_fastapi.apis.test_records_api import router as test_records_api_router
from lab_management_system_fastapi.impl.config import AppConfig, normalize_database_url
from lab_management_system_fastapi.impl.context import (
    RequestContext,
    reset_context,
    set_context,
)
from lab_management_system_fastapi.impl.directory import ConfigUserDirectory
from lab_management_system_fastapi.impl.errors import ApiError
from lab_management_system_fastapi.impl.menu_cache import (
    MembershipSnapshotCache,
    MenuSnapshotCache,
)
from lab_management_system_fastapi.impl.saas_client import SaasAuthClient, SaasMeClient
from lab_management_system_fastapi.impl.security import JwtIssuer

_ROUTERS = (
    auth_api_router,
    calculation_methods_api_router,
    contracts_api_router,
    frontend_bind_meta_api_router,
    inspection_catalog_api_router,
    inspection_dictionary_api_router,
    param_interfaces_api_router,
    receipts_api_router,
    report_names_api_router,
    samples_api_router,
    summary_api_router,
    technical_requirements_api_router,
    test_records_api_router,
)


def _strict_base(annotation: object) -> object | None:
    """取 Strict 注记的基型（int/str/…）；非 Annotated-Strict 形状（含 Optional 包裹）返回 None。"""
    origin = get_origin(annotation)
    if origin is Union or origin is types.UnionType:
        members = [a for a in get_args(annotation) if a is not type(None)]
        return _strict_base(members[0]) if len(members) == 1 else None
    args = get_args(annotation)
    if args and any(isinstance(m, Strict) for m in args[1:]):
        base: object = args[0]
        return base
    return None


def _relax_strict_query_ints(router: APIRouter) -> None:
    """生成契约把 query 参数钉成 StrictInt/StrictStr；query 串恒是字符串，FastAPI+pydantic v2
    strict 模式拒收字面量 → 必 422（openapi-generator python-fastapi 缺陷，saas 仓实踩三轮）。
    组合根收口：本版 FastAPI include 走 _IncludedRouter 惰性物化，effective dependant 是
    请求期从 route.endpoint 重新分析出来的（改已构建的 dependant 无效），故在 include 前
    给 endpoint 挂改写后的 __signature__——Strict → lax 基型（Query alias/默认值原样保留）；
    body 内 Strict 语义不动；生成文件零改动（只改运行时函数属性）。
    """
    for route in router.routes:
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None:
            continue
        signature = inspect.signature(endpoint)
        changed = False
        params = []
        for param in signature.parameters.values():
            base = _strict_base(param.annotation)
            if base is None:
                params.append(param)
                continue
            params.append(param.replace(annotation=base))
            changed = True
        if changed:
            endpoint.__signature__ = signature.replace(parameters=params)


def create_app(config: AppConfig, engine: Engine | None = None) -> FastAPI:
    """装配完整应用。测试注入内存 engine（mock-friendly）；生产从 config.database_url 建。

    认证域（批1）是内存目录不连库；engine 照 saas 镜像惰性创建，业务批（批2 起）接入。
    """
    db_engine = (
        engine
        if engine is not None
        else create_engine(normalize_database_url(config.database_url), pool_pre_ping=True)
    )
    app = FastAPI(title="实验室管理系统", version="0.1.0")
    app.state.config = config
    app.state.engine = db_engine
    app.state.session_factory = sessionmaker(bind=db_engine, expire_on_commit=False)
    app.state.jwt = JwtIssuer(config)
    app.state.directory = ConfigUserDirectory(config.auth_dev_password)
    app.state.menu_cache = MenuSnapshotCache()
    app.state.membership_cache = MembershipSnapshotCache()
    # SSO 测试缝：单测以 fake 覆盖这两个属性（REQ-2026-002 §6；saas 真连归批6 live）
    app.state.saas_auth = SaasAuthClient(config)
    app.state.saas_me = SaasMeClient(config)

    # CORS 白名单（springboot SecurityConfig.corsConfigurationSource 镜像）：
    # 显式 origin（非 *）+ credentials —— 前端 axios withCredentials=true 要求回显
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 家族健康探针（contract-test fnReporter healthcheck 目标；rails health#show 镜像）。
    # 基建端点不入功能树（rails 先例），匿名 200 纯探针、无 body、不泄运行面信息。
    @app.get("/health", include_in_schema=False)
    async def _health() -> Response:
        return Response(status_code=200)

    @app.middleware("http")
    async def _request_context(
        request: Request[State], call_next: Callable[[Request[State]], Awaitable[Response]]
    ) -> Response:
        session = request.app.state.session_factory()
        token = set_context(
            RequestContext(request=request, session=session, config=request.app.state.config)
        )
        try:
            response = await call_next(request)
        finally:
            reset_context(token)
            session.close()
        # 生成区路由对 204 端点只声明了 responses 没声明 status_code，FastAPI 回 200 null；
        # 家族契约是 204 空体（springboot logout/junctionService noContent 参照）——
        # 组合根收口，不动生成区（saas 仓同款）。
        # 批1：POST /api/auth/logout；
        # 批2（REQ-2026-003）：字典四 junction link（POST …/links/*）、calc/techreq
        # delete、report-names 三 link 家族、param-interfaces link、以及五面全部
        # DELETE（实体 delete 幂等/404 前置已在 impl resolve，能到这里的 200 null
        # 均为成功删除或 unlink no-op）。
        # 批3（REQ-2026-004）：catalog 码表四面 DELETE。
        if response.status_code == 200 and (
            (request.method == "POST" and request.url.path == "/api/auth/logout")
            or (request.method == "POST" and request.url.path.startswith("/api/inspection/links/"))
            or (
                request.method == "POST" and request.url.path.startswith("/api/report-names/links/")
            )
            or (request.method == "POST" and request.url.path == "/api/param-interfaces/links")
            or (request.method == "DELETE" and request.url.path.startswith("/api/inspection/"))
            or (
                request.method == "DELETE"
                and request.url.path.startswith("/api/calculation-methods/")
            )
            or (
                request.method == "DELETE"
                and request.url.path.startswith("/api/technical-requirements/")
            )
            or (request.method == "DELETE" and request.url.path.startswith("/api/report-names/"))
            or (
                request.method == "DELETE" and request.url.path.startswith("/api/param-interfaces/")
            )
            or (request.method == "DELETE" and request.url.path.startswith("/api/catalog/"))
        ):
            return Response(status_code=204)
        return response

    # starlette 位置传参调 handler（_exception_handler.py:59），下划线前缀参数安全
    @app.exception_handler(ApiError)
    async def _handle_api_error(_request: Request[State], exc: ApiError) -> JSONResponse:
        # 家族 ErrorResponse 形状 {code,message}（springboot GlobalExceptionHandler 镜像）
        return JSONResponse(
            status_code=exc.status_code, content={"code": exc.code, "message": exc.message}
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(
        _request: Request[State], exc: RequestValidationError
    ) -> JSONResponse:
        # 契约必填/类型不符：fastapi 校验层默认 422 {detail:[…]}，但家族契约面统一
        # springboot @Valid 口径 400 BAD_REQUEST {code,message}（saas 仓 CT live 实裁）。
        # message 取首违字段「field: msg」。
        first = exc.errors()[0]
        field = ".".join(str(p) for p in first.get("loc", ()) if p not in ("body", "query", "path"))
        return JSONResponse(
            status_code=400,
            content={"code": "BAD_REQUEST", "message": f"{field}: {first.get('msg', '')}"},
        )

    for router in _ROUTERS:
        _relax_strict_query_ints(router)
        app.include_router(router)
    return app


_APP: FastAPI | None = None


def __getattr__(name: str) -> FastAPI:
    """PEP 562：``app`` 惰性构建（读 env fail-fast 在首次访问，不在 import）。"""
    if name == "app":
        global _APP
        if _APP is None:
            _APP = create_app(AppConfig.from_env())
        return _APP
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
