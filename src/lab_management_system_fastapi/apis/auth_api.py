# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from lab_management_system_fastapi.apis.auth_api_base import BaseAuthApi
import lab_management_system_fastapi.impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from lab_management_system_fastapi.models.extra_models import TokenModel  # noqa: F401
from pydantic import StrictStr
from typing import Any, List
from lab_management_system_fastapi.models.auth_logout_request import AuthLogoutRequest
from lab_management_system_fastapi.models.current_user_session import CurrentUserSession
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.login_request import LoginRequest
from lab_management_system_fastapi.models.login_response import LoginResponse
from lab_management_system_fastapi.models.menu_node import MenuNode
from lab_management_system_fastapi.models.o_auth_response_type import OAuthResponseType
from lab_management_system_fastapi.models.permission_set import PermissionSet
from lab_management_system_fastapi.models.refresh_token_request import RefreshTokenRequest
from lab_management_system_fastapi.models.sso_callback_request import SsoCallbackRequest
from lab_management_system_fastapi.models.sso_redirect import SsoRedirect
from lab_management_system_fastapi.models.switch_tenant_request import SwitchTenantRequest


router = APIRouter()

ns_pkg = lab_management_system_fastapi.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/api/auth/login",
    responses={
        200: {"model": LoginResponse, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["auth"],
    response_model_by_alias=True,
)
async def auth_login(
    login_request: LoginRequest = Body(None, description=""),
) -> LoginResponse:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().auth_login(login_request)


@router.post(
    "/api/auth/logout",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["auth"],
    response_model_by_alias=True,
)
async def auth_logout(
    auth_logout_request: AuthLogoutRequest = Body(None, description=""),
) -> None:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().auth_logout(auth_logout_request)


@router.get(
    "/api/auth/me",
    responses={
        200: {"model": CurrentUserSession, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["auth"],
    response_model_by_alias=True,
)
async def auth_get_current_user(
) -> CurrentUserSession:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().auth_get_current_user()


@router.get(
    "/api/auth/menus",
    responses={
        200: {"model": List[MenuNode], "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["auth"],
    response_model_by_alias=True,
)
async def auth_get_menus(
) -> List[MenuNode]:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().auth_get_menus()


@router.post(
    "/api/auth/native-login",
    responses={
        200: {"model": LoginResponse, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["auth"],
    response_model_by_alias=True,
)
async def auth_native_login(
    login_request: LoginRequest = Body(None, description=""),
) -> LoginResponse:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().auth_native_login(login_request)


@router.get(
    "/api/auth/permissions",
    responses={
        200: {"model": PermissionSet, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["auth"],
    response_model_by_alias=True,
)
async def auth_get_permissions(
) -> PermissionSet:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().auth_get_permissions()


@router.post(
    "/api/auth/refresh",
    responses={
        200: {"model": LoginResponse, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["auth"],
    response_model_by_alias=True,
)
async def auth_refresh(
    refresh_token_request: RefreshTokenRequest = Body(None, description=""),
) -> LoginResponse:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().auth_refresh(refresh_token_request)


@router.get(
    "/api/auth/sso/authorize",
    responses={
        200: {"model": SsoRedirect, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["auth"],
    response_model_by_alias=True,
)
async def auth_sso_authorize(
    response_type: OAuthResponseType = Query(None, description="", alias="response_type"),
    client_id: StrictStr = Query(None, description="", alias="client_id"),
    redirect_uri: StrictStr = Query(None, description="", alias="redirect_uri"),
    state: StrictStr = Query(None, description="", alias="state"),
) -> SsoRedirect:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().auth_sso_authorize(response_type, client_id, redirect_uri, state)


@router.post(
    "/api/auth/sso/callback",
    responses={
        200: {"model": LoginResponse, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["auth"],
    response_model_by_alias=True,
)
async def auth_sso_callback(
    sso_callback_request: SsoCallbackRequest = Body(None, description=""),
) -> LoginResponse:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().auth_sso_callback(sso_callback_request)


@router.post(
    "/api/auth/switch-tenant",
    responses={
        200: {"model": LoginResponse, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["auth"],
    response_model_by_alias=True,
)
async def auth_switch_tenant(
    switch_tenant_request: SwitchTenantRequest = Body(None, description=""),
) -> LoginResponse:
    if not BaseAuthApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAuthApi.subclasses[0]().auth_switch_tenant(switch_tenant_request)
