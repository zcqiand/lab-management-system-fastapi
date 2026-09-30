"""AuthApiImpl —— 认证域 10 端点实现，语义逐条对照 lab-springboot AuthService.java
（REQ-2026-002 T-3；注释标注参照方法）。

组装件从 ``app.state`` 取（组合根装配，见 app.py）：directory / jwt / saas_auth /
saas_me / menu_cache / membership_cache / config。生成 router 每请求
``BaseAuthApi.subclasses[0]()`` 无参实例化本类，故构造器不接依赖。
"""

from __future__ import annotations

import logging
from urllib.parse import quote_plus

from lab_management_system_fastapi.apis.auth_api_base import BaseAuthApi
from lab_management_system_fastapi.impl.config import AppConfig
from lab_management_system_fastapi.impl.context import get_context
from lab_management_system_fastapi.impl.directory import ConfigUserDirectory
from lab_management_system_fastapi.impl.errors import (
    BadRequestError,
    InvalidCredentialsError,
    InvalidGrantError,
    MenusUnavailableError,
    NotFoundError,
    SaasUpstreamError,
    UnauthorizedClientError,
)
from lab_management_system_fastapi.impl.menu_cache import (
    MembershipSnapshotCache,
    MenuSnapshotCache,
    map_saas_menus,
)
from lab_management_system_fastapi.impl.saas_client import (
    SaasAuthClient,
    SaasCurrentUser,
    SaasMeClient,
    SaasPlatformTenant,
    SaasTenantMembership,
)
from lab_management_system_fastapi.impl.security import JwtIssuer, require_bearer
from lab_management_system_fastapi.models.auth_logout_request import AuthLogoutRequest
from lab_management_system_fastapi.models.current_user import CurrentUser
from lab_management_system_fastapi.models.current_user_session import CurrentUserSession
from lab_management_system_fastapi.models.login_request import LoginRequest
from lab_management_system_fastapi.models.login_response import LoginResponse
from lab_management_system_fastapi.models.menu_node import MenuNode
from lab_management_system_fastapi.models.my_tenant import MyTenant
from lab_management_system_fastapi.models.o_auth_response_type import OAuthResponseType
from lab_management_system_fastapi.models.permission_set import PermissionSet
from lab_management_system_fastapi.models.refresh_token_request import RefreshTokenRequest
from lab_management_system_fastapi.models.sso_callback_request import SsoCallbackRequest
from lab_management_system_fastapi.models.sso_redirect import SsoRedirect
from lab_management_system_fastapi.models.switch_tenant_request import SwitchTenantRequest

log = logging.getLogger(__name__)

# 密码登录缺省 refresh token 载荷（AuthService.session "dev-placeholder" 镜像：
# dev 用户无 saas 身份，refresh 走 saas 会 4xx → 前端回密码重登）
_DEV_PLACEHOLDER_REFRESH = "dev-placeholder"

# lab 家族在 saas 注册的 appCode（seeds apps.json，AuthService.LAB_APP_CODE 镜像）
_LAB_APP_CODE = "lab-management"

# msw 权限集（admin 全量 11 项，AuthService.DEMO_PERMISSIONS 镜像）
_DEMO_PERMISSIONS = [
    "contract:read",
    "contract:write",
    "sample:read",
    "sample:write",
    "report:read",
    "report:write",
    "report:issue",
    "inspection:read",
    "inspection:write",
    "audit:read",
    "*",
]


class AuthApiImpl(BaseAuthApi):
    """M00.F01/F02 + M01.F04/F05（ADR-0008：配置式目录 + HS256 JWT + saas SSO）。"""

    # === M01.F05.I01 密码登录（AuthService.login 镜像） ===

    async def auth_login(self, login_request: LoginRequest) -> LoginResponse:
        state = self._state()
        body = login_request
        username = (body.username or "").strip() if body is not None else ""
        password = body.password if body is not None else ""
        if not username or not password:
            raise BadRequestError("username and password are required")
        if not state.directory.check_password(username, password):
            raise InvalidCredentialsError("Invalid username or password")
        user = state.directory.find_by_username(username)
        if user is None:
            raise InvalidCredentialsError("Invalid username or password")
        # 密码登录 dev 用户无 saas 身份 → 服务账号拉菜单快照；失败只 warn 不阻塞登录
        self._cache_menus_with_service_account(user.id)
        return self._session(state, user, None, None, None)

    async def auth_native_login(self, login_request: LoginRequest) -> LoginResponse:
        # springboot AuthController native-login 直通 service.login（同源非浏览器通道）
        return await self.auth_login(login_request)

    # === M01.F05.I05 登出（无状态 JWT：服务端无 session store，204 由组合根收口） ===

    async def auth_logout(self, _auth_logout_request: AuthLogoutRequest) -> None:
        # 生成基类签名占位参：无状态登出不消费（镜像 springboot 空 service.logout）
        return None

    # === M00.F01.I01 当前会话（AuthService.me 镜像） ===

    async def auth_get_current_user(self) -> CurrentUserSession:
        state = self._state()
        claims = require_bearer(get_context(), state.jwt)
        user = self._resolve_user(state.directory, claims)
        saas_refresh = state.directory.get_saas_refresh_token(user.id)
        if saas_refresh:
            # SSO 用户必须返回 saas memberships 体系（跨体系失配防御）；miss 401 走 refresh 自愈
            cached_tenants = state.membership_cache.get(user.id)
            if cached_tenants is None:
                raise InvalidCredentialsError(
                    "membership snapshot unavailable for user "
                    f"{user.id} (cache miss); refresh required"
                )
            tenant_claim = claims.get("tenant_id")
            current_tenant_id = (
                str(tenant_claim) if tenant_claim is not None else cached_tenants[0].tenant_id
            )
            return CurrentUserSession(
                user=user, tenants=cached_tenants, currentTenantId=current_tenant_id
            )
        tenant_claim = claims.get("tenant_id")
        current_tenant_id = (
            str(tenant_claim)
            if tenant_claim is not None
            else state.directory.default_tenant().tenant_id
        )
        return CurrentUserSession(
            user=user,
            tenants=state.directory.tenants_of(user.username),
            currentTenantId=current_tenant_id,
        )

    # === M00.F02.I01 选租户换发（AuthService.switchTenant 镜像） ===

    async def auth_switch_tenant(self, switch_tenant_request: SwitchTenantRequest) -> LoginResponse:
        state = self._state()
        claims = require_bearer(get_context(), state.jwt)
        user = self._resolve_user(state.directory, claims)
        tenant_id = switch_tenant_request.tenant_id if switch_tenant_request is not None else ""
        target = state.directory.find_by_tenant_id(tenant_id)
        if target is None:
            raise NotFoundError("Tenant not found")
        return self._session(state, user, target.tenant_id, None, None)

    # === M01.F04.I01 动态菜单（AuthService.menus 镜像：miss 503，demo 兜底已删口径） ===

    async def auth_get_menus(self) -> list[MenuNode]:
        state = self._state()
        claims = require_bearer(get_context(), state.jwt)
        sub = claims.get("sub")
        sub_str = str(sub) if sub is not None else None
        snapshot = state.menu_cache.get(sub_str)
        if snapshot is None:
            raise MenusUnavailableError(
                f"menu snapshot unavailable for user {sub_str}; re-login to refresh"
            )
        return snapshot

    # === M01.F04.I02 权限集（AuthService.permissions 镜像：admin 全量 11 项） ===

    async def auth_get_permissions(self) -> PermissionSet:
        require_bearer(get_context(), self._state().jwt)
        return PermissionSet(permissions=list(_DEMO_PERMISSIONS))

    # === M01.F05.I04 刷新 token（AuthService.refresh 镜像） ===

    async def auth_refresh(self, refresh_token_request: RefreshTokenRequest) -> LoginResponse:
        state = self._state()
        body = refresh_token_request
        if body is None or body.refresh_token is None:
            raise InvalidCredentialsError("missing refresh_token")
        try:
            claims = state.jwt.verify(body.refresh_token)
        except InvalidCredentialsError as exc:
            raise InvalidCredentialsError(f"invalid refresh_token: {exc.message}") from exc
        if claims.get("typ") != "refresh":
            raise InvalidCredentialsError("invalid refresh_token: not a refresh token")
        tenant_id = claims.get("tenant_id")
        saas_refresh = claims.get("saas_refresh_token")
        if not saas_refresh:
            raise InvalidCredentialsError("invalid refresh_token: missing saas_refresh_token claim")
        # 走 saas /oauth/token grantType=refresh_token；saas 失败包 401（前端触发重登）
        try:
            token = state.saas_auth.token("refresh_token", None, str(saas_refresh), None)
        except (InvalidGrantError, UnauthorizedClientError, SaasUpstreamError) as exc:
            raise InvalidCredentialsError(f"saas refresh failed: {exc.message}") from exc
        saas_user = state.saas_me.whoami(token.access_token)
        memberships = state.saas_me.list_my_tenants(token.access_token)
        # 新部署/重启后 upserted 目录为空 → upsert 自愈（跟 ssoCallback 同款兜底）
        lab_user = self._upsert_by_email(state.directory, saas_user)
        # rotate-once：新 saas refresh token 必须存回目录
        state.directory.set_saas_refresh_token(lab_user.id, token.refresh_token)
        self._cache_menus(state, lab_user.id, token.access_token)
        name_by_id = self._fetch_tenant_names(state, lab_user.id, token.access_token)
        tenants = self._tenants_from(memberships, name_by_id)
        state.membership_cache.put(lab_user.id, tenants)
        return self._session(
            state, lab_user, str(tenant_id) if tenant_id else None, tenants, token.refresh_token
        )

    # === M01.F05.I02 SSO 跳转（AuthService.ssoAuthorize 镜像，2026-08-29 跳板形收敛） ===

    async def auth_sso_authorize(
        self,
        _response_type: OAuthResponseType,
        _client_id: str,
        redirect_uri: str,
        state: str,
    ) -> SsoRedirect:
        cfg = self._state().config
        # service 只消费 redirect_uri + state（response_type/client_id 参数被忽略——
        # AuthController 镜像；URL 里的 client_id 取 config 不取 query）。
        # ADR-0019 + RFC 6749 §4.1.1：redirect_uri 由前端发起，缺失 fail-fast 不兜 env
        # （2026-09-23 跨前端事故：硬用 env 回调地址导致别的前端拿不到 code）。
        if redirect_uri is None or redirect_uri.strip() == "":
            raise BadRequestError("missing redirect_uri")
        state_value = state if state is not None else ""
        authorize_url = (
            f"{cfg.effective_login_url}/login"
            f"?redirect_uri={quote_plus(redirect_uri)}"
            f"&state={quote_plus(state_value)}"
            f"&client_id={quote_plus(cfg.saas_client_id)}"
        )
        return SsoRedirect(authorizeUrl=authorize_url, state=state_value)

    # === M01.F05.I03 SSO 回调（AuthService.ssoCallback 镜像） ===

    async def auth_sso_callback(self, sso_callback_request: SsoCallbackRequest) -> LoginResponse:
        state = self._state()
        body = sso_callback_request
        if body is None:
            raise BadRequestError("missing body")
        # 契约 SsoCallbackRequest.redirect_uri 必填 —— springboot 的 callbackRedirectBase
        # 兜底分支在生成契约下不可达（镜像差异点，env 仍保留供跳板语义对齐）
        token = state.saas_auth.token("authorization_code", body.code, None, body.redirect_uri)
        saas_user = state.saas_me.whoami(token.access_token)
        memberships = state.saas_me.list_my_tenants(token.access_token)
        lab_user = self._upsert_by_email(state.directory, saas_user)
        # 菜单/成员资格快照：瞬时持有 saas accessToken 的窗口顺手拉齐；失败只 warn 不阻塞登录
        self._cache_menus(state, lab_user.id, token.access_token)
        state.directory.set_saas_refresh_token(lab_user.id, token.refresh_token)
        name_by_id = self._fetch_tenant_names(state, lab_user.id, token.access_token)
        tenants = self._tenants_from(memberships, name_by_id)
        state.membership_cache.put(lab_user.id, tenants)
        # token 带 tenant_id claim（whoami currentTenantId）——me() 不再落 demo 默认租户
        return self._session(
            state, lab_user, saas_user.current_tenant_id, tenants, token.refresh_token
        )

    # === 内部 helpers（AuthService 私有方法镜像） ===

    def _state(self) -> _AppState:
        ctx = get_context()
        return _AppState(
            directory=ctx.request.app.state.directory,
            jwt=ctx.request.app.state.jwt,
            saas_auth=ctx.request.app.state.saas_auth,
            saas_me=ctx.request.app.state.saas_me,
            menu_cache=ctx.request.app.state.menu_cache,
            membership_cache=ctx.request.app.state.membership_cache,
            config=ctx.config,
        )

    def _resolve_user(
        self, directory: ConfigUserDirectory, claims: dict[str, object]
    ) -> CurrentUser:
        """sub claim 解析 lab 用户：id → email（SSO 写入路径）→ username（密码登录路径）。"""
        sub = claims.get("sub")
        sub_str = str(sub) if sub is not None else ""
        if not sub_str:
            raise InvalidCredentialsError("missing sub claim")
        user = (
            directory.find_by_id(sub_str)
            or directory.find_by_email(sub_str)
            or directory.find_by_username(sub_str)
        )
        if user is None:
            raise InvalidCredentialsError(f"unknown user: {sub_str}")
        return user

    def _upsert_by_email(
        self, directory: ConfigUserDirectory, saas_user: SaasCurrentUser
    ) -> CurrentUser:
        # username → email 桥接（ADR-0008）；角色镜像 springboot 固定 "viewer"
        found = directory.find_by_email(saas_user.email)
        if found is not None:
            return found
        return directory.upsert(saas_user.id, saas_user.email, saas_user.display_name, "viewer")

    def _cache_menus_with_service_account(self, user_id: str) -> None:
        """密码登录路径：服务账号登 saas 换 token 拉 /me/menus；失败只 warn（菜单不阻塞登录）。"""
        state = self._state()
        try:
            token = state.saas_auth.service_login()
            self._cache_menus(state, user_id, token.access_token)
        except (InvalidGrantError, UnauthorizedClientError, SaasUpstreamError) as exc:
            log.warning(
                "service-account menu snapshot failed for user %s: %s", user_id, exc.message
            )

    def _cache_menus(self, state: _AppState, user_id: str, saas_access_token: str) -> None:
        if not user_id or not saas_access_token:
            return
        try:
            snapshot = state.saas_me.list_my_menus(saas_access_token, _LAB_APP_CODE)
            state.menu_cache.put(user_id, map_saas_menus(snapshot))
        except (InvalidGrantError, UnauthorizedClientError, SaasUpstreamError) as exc:
            log.warning("menu snapshot fetch failed for user %s: %s", user_id, exc.message)

    def _fetch_tenant_names(
        self, state: _AppState, user_id: str, saas_access_token: str
    ) -> dict[str, SaasPlatformTenant]:
        """租户显示名富化（2026-09-15 家族语义）：memberships 只有 tenantId，
        趁瞬时 token 窗口拉平台租户列表填真名；失败降级 name=tenantId 只 warn。"""
        try:
            rows = state.saas_me.list_platform_tenants(saas_access_token)
        except (InvalidGrantError, UnauthorizedClientError, SaasUpstreamError) as exc:
            log.warning("tenant name lookup failed for user %s: %s", user_id, exc.message)
            return {}
        return {t.id: t for t in rows if t.id}

    def _tenants_from(
        self,
        list_of_memberships: list[SaasTenantMembership],
        name_by_id: dict[str, SaasPlatformTenant],
    ) -> list[MyTenant]:
        """memberships → MyTenant：命中富化 code=tenantKey/name=name；miss 降级双双=tenantId
        （切换器最差显示 UUID，不空）。"""
        tenants: list[MyTenant] = []
        for m in list_of_memberships:
            t = name_by_id.get(m.tenant_id)
            tenants.append(
                MyTenant(
                    tenantId=m.tenant_id,
                    code=t.tenant_key if t is not None and t.tenant_key else m.tenant_id,
                    name=t.name if t is not None and t.name else m.tenant_id,
                    roleIds=list(m.role_ids),
                )
            )
        return tenants

    def _session(
        self,
        state: _AppState,
        user: CurrentUser,
        tenant_id: str | None,
        tenants: list[MyTenant] | None,
        saas_refresh_token: str | None,
    ) -> LoginResponse:
        access_token = state.jwt.issue(user.id, tenant_id)
        refresh_token = state.jwt.issue_refresh(
            user.id,
            saas_refresh_token if saas_refresh_token else _DEV_PLACEHOLDER_REFRESH,
        )
        use_tenants = tenants if tenants is not None else state.directory.tenants_of(user.username)
        return LoginResponse(
            token=access_token, refreshToken=refresh_token, user=user, tenants=use_tenants
        )


class _AppState:
    """impl 缝用到的 app.state 子集（便于类型标注与 fake 注入）。"""

    __slots__ = (
        "config",
        "directory",
        "jwt",
        "saas_auth",
        "saas_me",
        "menu_cache",
        "membership_cache",
    )

    def __init__(
        self,
        config: AppConfig,
        directory: ConfigUserDirectory,
        jwt: JwtIssuer,
        saas_auth: SaasAuthClient,
        saas_me: SaasMeClient,
        menu_cache: MenuSnapshotCache,
        membership_cache: MembershipSnapshotCache,
    ) -> None:
        self.config = config
        self.directory = directory
        self.jwt = jwt
        self.saas_auth = saas_auth
        self.saas_me = saas_me
        self.menu_cache = menu_cache
        self.membership_cache = membership_cache
