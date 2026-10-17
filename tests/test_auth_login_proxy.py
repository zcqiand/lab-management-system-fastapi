"""登录账密校验代理 saas IdP 单测（REQ-2026-023 T-5，M01.F05.I01/I06 同源 service.login）。

锁五仓统一语义：出站 user_login（clientId=saas_client_id=LAB_SAAS_CLIENT_ID，账密原值
透传）；saas 200 → user/tenants 映射自 saas 响应（租户名富化 best-effort 降级
name=tenantId）；lab 自家 JWT 重签（tenant_id=saas currentTenantId ?? 首租户）；
refresh 维持 dev-placeholder；错误映射：saas 4xx → 401 INVALID_CREDENTIALS，
5xx/不可达 → 502 SAAS_UNAVAILABLE。
"""

from __future__ import annotations

import jwt as pyjwt
import pytest
from fastapi.testclient import TestClient

from lab_management_system_fastapi.app import create_app
from lab_management_system_fastapi.impl.config import AppConfig
from lab_management_system_fastapi.impl.errors import InvalidGrantError, SaasUpstreamError
from lab_management_system_fastapi.impl.saas_client import (
    SaasAuthClient,
    SaasLoginResponse,
    SaasPlatformTenant,
    TokenResponse,
)

TEST_KEY = "dev-key-32-bytes-minimum-length!"
ISSUER = "lab-management-fastapi"


def make_config() -> AppConfig:
    # saas_client_id 与 service_client_id 刻意不同值：锁出站 clientId 取 OAuth client id
    return AppConfig(
        database_url="postgresql://lab:pw@localhost:5432/lab_unused_proxy",
        jwt_signing_key=TEST_KEY,
        jwt_issuer=ISSUER,
        jwt_ttl_seconds=3600,
        jwt_refresh_ttl_seconds=604800,
        saas_base_url="http://saas.test:5107",
        sso_login_url="",
        saas_client_id="oauth-client-id",
        saas_client_secret="lab-secret",
        saas_default_tenant_id="TENANT-001",
        sso_callback_redirect="http://lab.test:5202",
        saas_service_user="svc",
        saas_service_password="svc-pw",
        saas_service_client_id="lab-management",
        cors_allowed_origins="http://localhost:5201,http://localhost:5202",
    )


class RecordingSaasAuth:
    """记录出站账密、可注错的 user_login 替身；service_login/token 走最小 stub。"""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.failure: Exception | None = None

    def user_login(self, username: str, password: str) -> SaasLoginResponse:
        self.calls.append((username, password))
        if self.failure is not None:
            raise self.failure
        return SaasLoginResponse.model_validate(
            {
                "user": {
                    "id": "saas-user-alice",
                    "username": "alice",
                    "email": "alice@saas.local",
                },
                "availableTenants": [
                    {"tenantId": "TEN-1", "roleIds": ["admin"], "status": "active"},
                    {"tenantId": "TEN-2", "roleIds": ["technician"], "status": "active"},
                ],
                "accessToken": "u-at",
                "refreshToken": "u-rt",
                "userId": "saas-user-alice",
            }
        )

    def service_login(self) -> TokenResponse:
        return TokenResponse(access_token="svc-access", refresh_token="svc-refresh")

    def token(
        self,
        _grant_type: str,
        _code: str | None = None,
        _refresh_token: str | None = None,
        _redirect_uri: str | None = None,
    ) -> TokenResponse:
        return TokenResponse(access_token="saas-access", refresh_token="saas-refresh")


class EnrichingSaasMe:
    """平台租户只富化 TEN-1（TEN-2 不在列表 → 降级路径）；菜单树恒空。"""

    def list_platform_tenants(self, _access_token: str) -> list[SaasPlatformTenant]:
        return [SaasPlatformTenant(id="TEN-1", name="市检测中心", tenantKey="city")]

    def list_my_menus(self, _access_token: str, _app_code: str) -> list[object]:
        return []


def make_client(saas_auth: RecordingSaasAuth) -> TestClient:
    app = create_app(make_config())
    app.state.saas_auth = saas_auth
    app.state.saas_me = EnrichingSaasMe()
    return TestClient(app)


def _decode(token: str) -> dict:
    return pyjwt.decode(
        token, TEST_KEY, algorithms=["HS256"], issuer=ISSUER, options={"verify_aud": False}
    )


@pytest.mark.fn("M01.F05.I01")
def test_login_proxies_saas_and_resigns_lab_jwt() -> None:
    auth = RecordingSaasAuth()
    resp = make_client(auth).post(
        "/api/auth/login", json={"username": "alice", "password": "pw-123"}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # 出站透传：账密原值进 user_login
    assert auth.calls == [("alice", "pw-123")]
    # user 映射自 saas（displayName 回退 username）；roleCode=首租户 roleIds[0]
    assert body["user"] == {
        "id": "saas-user-alice",
        "username": "alice",
        "displayName": "alice",
        "roleCode": "admin",
    }
    # tenants 四字段 + 富化真名/tenantKey（TEN-2 不在平台列表 → 降级 tenantId）
    assert body["tenants"] == [
        {"tenantId": "TEN-1", "code": "city", "name": "市检测中心", "roleIds": ["admin"]},
        {"tenantId": "TEN-2", "code": "TEN-2", "name": "TEN-2", "roleIds": ["technician"]},
    ]
    # lab 自家 JWT 重签：tenant_id=首租户
    access = _decode(body["token"])
    assert access["sub"] == "saas-user-alice"
    assert access["tenant_id"] == "TEN-1"
    # refresh 维持 dev-placeholder（不透传 saas refreshToken）
    refresh = _decode(body["refreshToken"])
    assert refresh["saas_refresh_token"] == "dev-placeholder"


@pytest.mark.fn("M01.F05.I01")
def test_native_login_shares_proxy_path() -> None:
    auth = RecordingSaasAuth()
    resp = make_client(auth).post(
        "/api/auth/native-login", json={"username": "alice", "password": "pw-123"}
    )
    assert resp.status_code == 200
    assert auth.calls == [("alice", "pw-123")]


@pytest.mark.fn("M01.F05.I01")
def test_login_saas_4xx_is_401_invalid_credentials() -> None:
    auth = RecordingSaasAuth()
    auth.failure = InvalidGrantError('saas 400 {"error":"invalid_grant"}')
    resp = make_client(auth).post(
        "/api/auth/login", json={"username": "alice", "password": "wrong"}
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "INVALID_CREDENTIALS"


@pytest.mark.fn("M01.F05.I01")
def test_login_saas_unavailable_is_502_saas_unavailable() -> None:
    auth = RecordingSaasAuth()
    auth.failure = SaasUpstreamError("saas auth/login connect failed")
    resp = make_client(auth).post("/api/auth/login", json={"username": "alice", "password": "pw"})
    assert resp.status_code == 502
    assert resp.json()["code"] == "SAAS_UNAVAILABLE"


# === REQ-2026-023 live 回归（2026-10-11 五目标同时失败指纹） ===
# 现场：登录 sub=saas user id / tenant_id claim=saas 租户，但登录链不落
# directory upsert + membership 快照 → me/switch 的 _resolve_user 报
# unknown user 401；switch 归属校验写死 demo 字面量 → saas 租户 404。
# 契约：登录后 me/switch 必须与登录响应同一租户体系（2026-09-03 对齐约束：
# tenants.find(activeTenantId) 必命中）。

UUID_USER = "00000000-0000-0000-0000-b00000000001"


class UuidSaasAuth(RecordingSaasAuth):
    """live 回归替身：saas 真实租户是 UUID 形（live 实测），刻意不用 TEN-1 形——
    会与 demo 目录撞键掩盖失配（本测试的存在理由）。"""

    def user_login(self, username: str, password: str) -> SaasLoginResponse:
        self.calls.append((username, password))
        if self.failure is not None:
            raise self.failure
        return SaasLoginResponse.model_validate(
            {
                "user": {"id": UUID_USER, "username": "alice", "email": "alice@saas.local"},
                "availableTenants": [
                    {
                        "tenantId": "00000000-0000-0000-0000-000000000001",
                        "roleIds": ["admin"],
                        "status": "active",
                    },
                    {
                        "tenantId": "00000000-0000-0000-0000-000000000002",
                        "roleIds": ["technician"],
                        "status": "active",
                    },
                ],
                "accessToken": "u-at",
                "refreshToken": "u-rt",
                "userId": UUID_USER,
            }
        )


@pytest.mark.fn("M00.F01.I01", "M00.F02.I01")
def test_login_session_coherence_me_and_switch_stay_in_saas_tenant_system() -> None:
    client = make_client(UuidSaasAuth())
    resp = client.post("/api/auth/login", json={"username": "alice", "password": "pw-123"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    tid = body["tenants"][0]["tenantId"]
    assert tid == "00000000-0000-0000-0000-000000000001"
    bearer = {"Authorization": f"Bearer {body['token']}"}

    # me：resolve_user 必须能解析密码登录签发的 sub；租户与登录响应同体系
    me = client.get("/api/auth/me", headers=bearer)
    assert me.status_code == 200, me.text
    me_body = me.json()
    assert me_body["tenants"][0]["tenantId"] == tid
    assert len(me_body["tenants"]) == len(body["tenants"])

    # switch-tenant：登录响应里的租户可切 → 200 + 3 段真 JWT（tenant_id=目标租户）
    switched = client.post("/api/auth/switch-tenant", json={"tenantId": tid}, headers=bearer)
    assert switched.status_code == 200, switched.text
    switched_body = switched.json()
    assert len(switched_body["token"].split(".")) == 3
    assert _decode(switched_body["token"])["tenant_id"] == tid


@pytest.mark.fn("M01.F05.I01")
def test_saas_client_user_login_sends_oauth_client_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """出站 body clientId=OAuth client id（LAB_SAAS_CLIENT_ID），不是 service_client_id。"""
    captured: dict[str, object] = {}

    class FakeResp:
        status_code = 200
        text = "{}"

        def json(self) -> dict:
            return {
                "user": {"id": "u1", "username": "alice"},
                "availableTenants": [],
                "accessToken": "at",
            }

    def fake_request(_method: str, url: str, json: dict | None = None, **_kw: object) -> FakeResp:
        captured["url"] = url
        captured["json"] = json
        return FakeResp()

    monkeypatch.setattr(
        "lab_management_system_fastapi.impl.saas_client.httpx.request", fake_request
    )
    resp = SaasAuthClient(make_config()).user_login("alice", "pw-123")
    assert str(captured["url"]).endswith("/api/v1/auth/login")
    assert captured["json"] == {
        "username": "alice",
        "password": "pw-123",
        "clientId": "oauth-client-id",
    }
    assert resp.user is not None and resp.user.username == "alice"


# === 终审 I2 家族级修复：me 空租户快照空态（kotlin AuthSessionTest 同源镜像） ===


class ZeroTenantSaasAuth(RecordingSaasAuth):
    """零 active 租户用户：快照空列表 + token 无 tenant_id claim（oscar 非 alice）。"""

    def user_login(self, username: str, password: str) -> SaasLoginResponse:
        self.calls.append((username, password))
        if self.failure is not None:
            raise self.failure
        return SaasLoginResponse.model_validate(
            {
                "user": {
                    "id": "saas-user-oscar",
                    "username": "oscar",
                    "email": "oscar@saas.local",
                },
                "availableTenants": [],
                "accessToken": "u-at",
                "refreshToken": "u-rt",
                "userId": "saas-user-oscar",
            }
        )


@pytest.mark.fn("M00.F01.I01")
def test_me_empty_membership_snapshot_is_empty_current_tenant_not_500() -> None:
    # 空即空（tenants=[] + currentTenantId=""，禁 demo 兜底），非 IndexError → 500
    client = make_client(ZeroTenantSaasAuth())
    login = client.post("/api/auth/login", json={"username": "oscar", "password": "pw"})
    assert login.status_code == 200, login.text
    token = login.json()["token"]
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tenants"] == []
    assert body["currentTenantId"] == ""
