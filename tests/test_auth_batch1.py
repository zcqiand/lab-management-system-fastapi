"""批1 会话与认证断言测试（REQ-2026-002 T-1，red-first）。

- 内存目录 + fake saas client 注入 ``app.state.saas_auth/saas_me`` 缝（REQ §6：
  SSO 簇以契约形状锁为主，saas 真连归批6 live）；
- 认证域无 DB（springboot ConfigUserDirectory 内存目录镜像）：本批不需要 scratch 库
  （REQ T-1「PG 真库 scratch 种子」措辞承自 saas 模板，实现按内存目录口径，勘误随 T-5 收口）；
- 语义逐条对照 lab-springboot AuthService.java（注释标注参照行）。
"""

from __future__ import annotations

import jwt as pyjwt
import pytest
from fastapi.testclient import TestClient

from lab_management_system_fastapi.app import create_app
from lab_management_system_fastapi.impl.config import AppConfig
from lab_management_system_fastapi.impl.errors import InvalidGrantError
from lab_management_system_fastapi.impl.saas_client import (
    SaasCurrentUser,
    SaasMenuNode,
    SaasPlatformTenant,
    SaasTenantMembership,
    TokenResponse,
)

# 家族 dev 签名密钥（九仓共享 dev-key-32-bytes-minimum-length!，LabJwtSigner javadoc 参照）
TEST_KEY = "dev-key-32-bytes-minimum-length!"
ISSUER = "lab-management-fastapi"
DEV_PASSWORD = "dev123456"

FAKE_SAAS_TENANT_ID = "T-9"


def make_config() -> AppConfig:
    return AppConfig(
        # 认证域内存目录，批1 不连库
        database_url="postgresql://lab:pw@localhost:5432/lab_unused_batch1",
        jwt_signing_key=TEST_KEY,
        jwt_issuer=ISSUER,
        jwt_ttl_seconds=3600,
        jwt_refresh_ttl_seconds=604800,
        saas_base_url="http://saas.test:5107",
        sso_login_url="",  # 空 = 回落 saas_base_url（springboot effectiveLoginUrl 家族语义）
        saas_client_id="lab-management",
        saas_client_secret="lab-secret",
        saas_default_tenant_id="TENANT-001",
        sso_callback_redirect="http://lab.test:5202",
        saas_service_user="alice",
        saas_service_password=DEV_PASSWORD,
        saas_service_client_id="lab-management",
        auth_dev_password=DEV_PASSWORD,
        cors_allowed_origins="http://localhost:5201,http://localhost:5202",
    )


class FakeSaasAuth:
    """saas /api/v1/auth/login + /api/v1/oauth/token 替身（形状对齐 SaasAuthClient）。"""

    def __init__(self) -> None:
        self.token_calls: list[dict[str, str | None]] = []
        self._n = 0

    def service_login(self) -> TokenResponse:
        return TokenResponse(access_token="svc-access", refresh_token="svc-refresh")

    def token(
        self,
        grant_type: str,
        code: str | None = None,
        refresh_token: str | None = None,
        redirect_uri: str | None = None,
    ) -> TokenResponse:
        self.token_calls.append(
            {
                "grant_type": grant_type,
                "code": code,
                "refresh_token": refresh_token,
                "redirect_uri": redirect_uri,
            }
        )
        if refresh_token == "expired-saas-refresh":
            # saas 4xx 拒绝 → InvalidGrantError（GlobalExceptionHandler 映射 400 INVALID_GRANT，
            # refresh 路径再包 401 —— AuthService.refresh catch SaasAuthException 镜像）
            raise InvalidGrantError('saas 400 {"error":"invalid_grant"}')
        # rotate-once：每次签发递增的新 saas refresh（消费即轮换可观测）
        self._n += 1
        return TokenResponse(
            access_token=f"saas-access-{self._n}", refresh_token=f"saas-refresh-{self._n}"
        )


class FakeSaasMe:
    """saas /api/v1/me* 替身：bob@lab.dev 在 saas 侧隶属 T-9（technician）。"""

    def whoami(self, _access_token: str) -> SaasCurrentUser:
        return SaasCurrentUser(
            id="saas-user-1",
            email="bob@lab.dev",
            displayName="Bob",
            currentTenantId=FAKE_SAAS_TENANT_ID,
        )

    def list_my_tenants(self, _access_token: str) -> list[SaasTenantMembership]:
        return [SaasTenantMembership(tenantId=FAKE_SAAS_TENANT_ID, roleIds=["technician"])]

    def list_my_menus(self, _access_token: str, app_code: str) -> list[SaasMenuNode]:
        if app_code != "lab-management":
            return []
        return [
            SaasMenuNode(
                id="m2",
                code="audit",
                type="page",
                sortOrder=1,
            ),
            SaasMenuNode(
                id="m1",
                code="inspection",
                title="试验过程",
                type="group",
                sortOrder=2,
                children=[
                    SaasMenuNode(
                        id="m1-1", code="samples", title="接样管理", type="page", sortOrder=2
                    ),
                    SaasMenuNode(
                        id="m1-2", code="records", title="数据录入", type="page", sortOrder=1
                    ),
                ],
            ),
        ]

    def list_platform_tenants(self, _access_token: str) -> list[SaasPlatformTenant]:
        return [
            SaasPlatformTenant(id=FAKE_SAAS_TENANT_ID, name="第三方平台租户", tenantKey="t9"),
            SaasPlatformTenant(
                id="TENANT-001", name="市住建工程质量检测中心", tenantKey="city-lab"
            ),
        ]


@pytest.fixture()
def app_client() -> TestClient:
    app = create_app(make_config())
    app.state.saas_auth = FakeSaasAuth()
    app.state.saas_me = FakeSaasMe()
    return TestClient(app)


def login(client: TestClient, username: str = "alice", password: str = DEV_PASSWORD) -> dict:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


def decode(token: str) -> dict:
    """lab JWT 无 aud（PyJWT verify_aud=False 镜像 springboot verify 只验 sig/iss/exp）。"""
    return pyjwt.decode(
        token, TEST_KEY, algorithms=["HS256"], issuer=ISSUER, options={"verify_aud": False}
    )


# === M01.F05.I01 密码登录（+ native-login 同源直通） ===


@pytest.mark.fn("M01.F05.I01")
def test_login_ok(app_client: TestClient) -> None:
    body = login(app_client)
    assert body["user"] == {
        "id": "USER-A",
        "username": "alice",
        "displayName": "管理员",
        "roleCode": "admin",
    }
    assert {t["tenantId"] for t in body["tenants"]} == {"TENANT-001", "TENANT-002", "TENANT-003"}
    assert body["tenants"][0] == {
        "tenantId": "TENANT-001",
        "code": "city-lab",
        "name": "市住建工程质量检测中心",
        "roleIds": ["admin"],
    }
    access = decode(body["token"])
    assert access["typ"] == "access" and access["sub"] == "USER-A"
    assert "tenant_id" not in access  # 无选租户登录不带 claim（LabJwtSigner.issue 镜像）
    refresh = decode(body["refreshToken"])
    assert refresh["typ"] == "refresh" and refresh["saas_refresh_token"] == "dev-placeholder"


@pytest.mark.fn("M01.F05.I01")
def test_login_native_same_path(app_client: TestClient) -> None:
    # springboot AuthController native-login 直通 service.login（同源非浏览器通道，不另立树行）
    resp = app_client.post(
        "/api/auth/native-login", json={"username": "alice", "password": DEV_PASSWORD}
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["id"] == "USER-A"


@pytest.mark.fn("M01.F05.I01")
def test_login_bad_password_401(app_client: TestClient) -> None:
    resp = app_client.post("/api/auth/login", json={"username": "alice", "password": "wrong"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_CREDENTIALS"


@pytest.mark.fn("M01.F05.I01")
def test_login_missing_field_400(app_client: TestClient) -> None:
    # 契约必填缺失：fastapi 422 收口家族 400 BAD_REQUEST（组合根 handler）
    resp = app_client.post("/api/auth/login", json={"username": "alice"})
    assert resp.status_code == 400
    assert resp.json()["code"] == "BAD_REQUEST"


# === M01.F05.I05 登出（无状态 204） ===


@pytest.mark.fn("M01.F05.I05")
def test_logout_204(app_client: TestClient) -> None:
    resp = app_client.post("/api/auth/logout", json={"token": "whatever"})
    assert resp.status_code == 204
    assert resp.content == b""


# === M00.F01.I01 当前会话 ===


@pytest.mark.fn("M00.F01.I01")
def test_me_password_user(app_client: TestClient) -> None:
    token = login(app_client)["token"]
    resp = app_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["id"] == "USER-A"
    assert len(body["tenants"]) == 3
    assert (
        body["currentTenantId"] == "TENANT-001"
    )  # 无 claim → defaultTenant（AuthService.me 镜像）


@pytest.mark.fn("M00.F01.I01")
def test_me_requires_bearer(app_client: TestClient) -> None:
    assert app_client.get("/api/auth/me").status_code == 401
    resp = app_client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_CREDENTIALS"


def sso_login(client: TestClient) -> dict:
    """SSO 全链路（I03）：callback 换发 + upsert + 双快照缓存。

    契约 SsoCallbackRequest 必填 grant_type（springboot DTO 容 null 的契约差异点，
    记忆 fastapi-contract-required-fields-diverge）。
    """
    resp = client.post(
        "/api/auth/sso/callback",
        json={
            "grant_type": "authorization_code",
            "code": "one-time-code",
            "redirect_uri": "http://localhost:5201/login",
            "state": "s1",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.mark.fn("M00.F01.I01")
def test_me_sso_user_reads_membership_cache(app_client: TestClient) -> None:
    body = sso_login(app_client)
    token = body["token"]
    resp = app_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    me = resp.json()
    # SSO 用户走 saas memberships 体系（tenants.find(saas UUID) 跨体系失配防御，
    # AuthService.me 镜像）
    assert me["tenants"] == [
        {
            "tenantId": FAKE_SAAS_TENANT_ID,
            "code": "t9",
            "name": "第三方平台租户",
            "roleIds": ["technician"],
        }
    ]
    assert (
        me["currentTenantId"] == FAKE_SAAS_TENANT_ID
    )  # token tenant_id claim（whoami currentTenantId）


@pytest.mark.fn("M00.F01.I01")
def test_me_sso_user_cache_miss_401(app_client: TestClient) -> None:
    body = sso_login(app_client)
    # 模拟重启/TTL 过期：membership 快照丢、per-user saas refresh 仍在目录
    app_client.app.state.membership_cache._snapshots.clear()  # noqa: SLF001 测试缝
    resp = app_client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['token']}"})
    assert resp.status_code == 401
    assert "refresh required" in resp.json()["message"]


# === M00.F02.I01 选租户换发 ===


@pytest.mark.fn("M00.F02.I01")
def test_switch_tenant_reissues_token_with_claim(app_client: TestClient) -> None:
    token = login(app_client)["token"]
    resp = app_client.post(
        "/api/auth/switch-tenant",
        json={"tenantId": "TENANT-002"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert decode(body["token"])["tenant_id"] == "TENANT-002"
    assert (
        len(body["tenants"]) == 3
    )  # 租户列表全量回显（springboot session(user, target, null) 镜像）


@pytest.mark.fn("M00.F02.I01")
def test_switch_unknown_tenant_404(app_client: TestClient) -> None:
    token = login(app_client)["token"]
    resp = app_client.post(
        "/api/auth/switch-tenant",
        json={"tenantId": "TENANT-404"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"


# === M01.F04.I01 动态菜单 / I02 权限集 ===


@pytest.mark.fn("M01.F04.I01")
def test_menus_from_snapshot(app_client: TestClient) -> None:
    login(app_client)  # 密码登录触发服务账号菜单快照（cacheMenusWithServiceAccount 镜像）
    token = app_client.app.state.jwt.issue("USER-A", None)
    resp = app_client.get("/api/auth/menus", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    tree = resp.json()
    assert [n["id"] for n in tree] == ["m2", "m1"]  # sortOrder 升序
    assert tree[0]["label"] == "audit"  # title 缺省回落 code（SaasMenuMapper 镜像）
    assert tree[0]["icon"] == "file"  # page 缺省 icon
    group = tree[1]
    assert group["label"] == "试验过程" and group["icon"] == "resource"  # group 缺省 icon
    assert [c["id"] for c in group["children"]] == ["m1-2", "m1-1"]  # 子树 sortOrder 排序


@pytest.mark.fn("M01.F04.I01")
def test_menus_miss_503(app_client: TestClient) -> None:
    login(app_client)
    app_client.app.state.menu_cache._snapshots.clear()  # noqa: SLF001 测试缝：快照过期/重启
    token = app_client.app.state.jwt.issue("USER-A", None)
    resp = app_client.get("/api/auth/menus", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 503
    assert resp.json()["code"] == "MENUS_UNAVAILABLE"


@pytest.mark.fn("M01.F04.I02")
def test_permissions_admin_11(app_client: TestClient) -> None:
    token = login(app_client)["token"]
    resp = app_client.get("/api/auth/permissions", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["permissions"] == [
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


# === M01.F05.I04 刷新 token ===


@pytest.mark.fn("M01.F05.I04")
def test_refresh_via_saas_rotation(app_client: TestClient) -> None:
    body = sso_login(app_client)  # SSO 用户的 refresh token 内嵌真 saas refresh
    saas_auth: FakeSaasAuth = app_client.app.state.saas_auth
    resp = app_client.post("/api/auth/refresh", json={"refreshToken": body["refreshToken"]})
    assert resp.status_code == 200, resp.text
    assert saas_auth.token_calls[-1] == {
        "grant_type": "refresh_token",
        "code": None,
        "refresh_token": "saas-refresh-1",  # sso 回调存回的旧 saas refresh
        "redirect_uri": None,
    }
    new = resp.json()
    assert decode(new["refreshToken"])["saas_refresh_token"] == "saas-refresh-2"
    # rotate-once：新 saas refresh 必须存回目录（ConfigUserDirectory.setSaasRefreshToken 镜像）
    assert app_client.app.state.directory.get_saas_refresh_token("saas-user-1") == (
        "saas-refresh-2"
    )
    assert [t["tenantId"] for t in new["tenants"]] == [FAKE_SAAS_TENANT_ID]


@pytest.mark.fn("M01.F05.I04")
def test_refresh_saas_reject_401(app_client: TestClient) -> None:
    jwt_issuer = app_client.app.state.jwt
    bad = jwt_issuer.issue_refresh("USER-A", "expired-saas-refresh")
    resp = app_client.post("/api/auth/refresh", json={"refreshToken": bad})
    # saas 拒绝 → SecurityException("saas refresh failed: …")（AuthService.refresh catch 镜像）
    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_CREDENTIALS"


@pytest.mark.fn("M01.F05.I04")
def test_refresh_rejects_access_token(app_client: TestClient) -> None:
    token = login(app_client)["token"]
    resp = app_client.post("/api/auth/refresh", json={"refreshToken": token})
    assert resp.status_code == 401  # typ=access 不是 refresh token


# === M01.F05.I02 SSO 跳转（跳板形，2026-08-29 收敛） ===


@pytest.mark.fn("M01.F05.I02")
def test_sso_authorize_jump_board_shape(app_client: TestClient) -> None:
    resp = app_client.get(
        "/api/auth/sso/authorize",
        params={
            "response_type": "code",
            "client_id": "from-query-ignored",
            "redirect_uri": "http://localhost:5201/login",
            "state": "csrf-123",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["state"] == "csrf-123"  # 前端生成、原样透传（RFC 6749 §10.12）
    # 空 LAB_SSO_LOGIN_URL 回落 saas base；client_id 取 config 不取 query
    # （service 只消费 redirect_uri+state，AuthController 镜像）
    assert body["authorizeUrl"] == (
        "http://saas.test:5107/login"
        "?redirect_uri=http%3A%2F%2Flocalhost%3A5201%2Flogin"
        "&state=csrf-123&client_id=lab-management"
    )
    assert "from-query-ignored" not in body["authorizeUrl"]


@pytest.mark.fn("M01.F05.I02")
def test_sso_authorize_missing_redirect_400(app_client: TestClient) -> None:
    resp = app_client.get("/api/auth/sso/authorize", params={"state": "csrf-123"})
    assert resp.status_code == 400
    assert resp.json()["code"] == "BAD_REQUEST"


# === M01.F05.I03 SSO 回调（code 换 token + email upsert + 双快照） ===


@pytest.mark.fn("M01.F05.I03")
def test_sso_callback_full_flow(app_client: TestClient) -> None:
    body = sso_login(app_client)
    assert body["user"] == {
        "id": "saas-user-1",
        "username": "bob@lab.dev",  # upsert username=email（ADR-0008 桥接）
        "displayName": "Bob",
        "roleCode": "viewer",
    }
    assert decode(body["token"])["tenant_id"] == FAKE_SAAS_TENANT_ID
    assert decode(body["refreshToken"])["saas_refresh_token"] == "saas-refresh-1"
    assert [t["name"] for t in body["tenants"]] == ["第三方平台租户"]  # admin/tenants 富化
    # 菜单快照已进缓存 → /menus 可用
    resp = app_client.get("/api/auth/menus", headers={"Authorization": f"Bearer {body['token']}"})
    assert resp.status_code == 200


@pytest.mark.fn("M01.F05.I03")
def test_sso_callback_second_login_upserts_once(app_client: TestClient) -> None:
    first = sso_login(app_client)
    second = sso_login(app_client)
    assert (
        first["user"]["id"] == second["user"]["id"]
    )  # 按 email 键幂等（ConfigUserDirectory.upsert）
    directory = app_client.app.state.directory
    assert len(directory._upserted) == 1  # noqa: SLF001 测试缝


# === 基建（不挂 fn：/health 匿名探针 + CORS，家族镜像） ===


def test_health_anonymous() -> None:
    app = create_app(make_config())
    resp = TestClient(app).get("/health")
    assert resp.status_code == 200


def test_cors_preflight() -> None:
    app = create_app(make_config())
    resp = TestClient(app).options(
        "/api/auth/login",
        headers={
            "Origin": "http://localhost:5201",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == "http://localhost:5201"
    assert resp.headers["access-control-allow-credentials"] == "true"
