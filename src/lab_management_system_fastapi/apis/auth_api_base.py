# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

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


class BaseAuthApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseAuthApi.subclasses = BaseAuthApi.subclasses + (cls,)
    async def auth_login(
        self,
        login_request: LoginRequest,
    ) -> LoginResponse:
        ...


    async def auth_logout(
        self,
        auth_logout_request: AuthLogoutRequest,
    ) -> None:
        ...


    async def auth_get_current_user(
        self,
    ) -> CurrentUserSession:
        ...


    async def auth_get_menus(
        self,
    ) -> List[MenuNode]:
        ...


    async def auth_native_login(
        self,
        login_request: LoginRequest,
    ) -> LoginResponse:
        ...


    async def auth_get_permissions(
        self,
    ) -> PermissionSet:
        ...


    async def auth_refresh(
        self,
        refresh_token_request: RefreshTokenRequest,
    ) -> LoginResponse:
        ...


    async def auth_sso_authorize(
        self,
        response_type: OAuthResponseType,
        client_id: StrictStr,
        redirect_uri: StrictStr,
        state: StrictStr,
    ) -> SsoRedirect:
        """  SSO 跳转端点（RFC 6749 §4.1.1 授权码流）。返回跳板 URL 而非 302：客户端取   authorizeUrl 做 top-level navigation。    state 由前端生成并原样透传，回跳时前端比对，防 CSRF；redirect_uri 须在后端   白名单内（https 域名之外，原生客户端允许自定义 scheme），白名单配置随部署   env，不入契约；client_secret 仅后端持有，不出现在本契约。"""
        ...


    async def auth_sso_callback(
        self,
        sso_callback_request: SsoCallbackRequest,
    ) -> LoginResponse:
        ...


    async def auth_switch_tenant(
        self,
        switch_tenant_request: SwitchTenantRequest,
    ) -> LoginResponse:
        ...
