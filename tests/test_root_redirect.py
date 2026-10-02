"""根路径默认跳转 Swagger 基建冒烟（REQ-2026-008 T-1，red-first）。

不入功能树、不挂 fn ID（REQ §4 + ADR-0027 subset invariant：基建端点进树即红，
/health 同类先例）。基建测试同 test_auth_batch1 基建段口径：内存目录直连 app，
无 scratch 库依赖（跳转 /docs /openapi.json 三面零 DB 访问，mock-friendly 铁律）。
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from lab_management_system_fastapi.app import create_app
from lab_management_system_fastapi.impl.config import AppConfig

# 家族 dev 签名密钥（九仓共享 dev-key-32-bytes-minimum-length!，LabJwtSigner javadoc 参照）
TEST_KEY = "dev-key-32-bytes-minimum-length!"
ISSUER = "lab-management-fastapi"
DEV_PASSWORD = "dev123456"


def make_config() -> AppConfig:
    return AppConfig(
        # 基建三面零 DB 访问：dummy URL 不触库（sqlalchemy 惰性建引擎）
        database_url="postgresql://lab:pw@localhost:5432/lab_unused_infra",
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


def test_root_redirects_to_docs() -> None:
    resp = TestClient(create_app(make_config())).get("/", follow_redirects=False)
    assert resp.status_code == 307, resp.text
    assert resp.headers["location"] == "/docs"


def test_docs_renders_swagger_ui() -> None:
    resp = TestClient(create_app(make_config())).get("/docs")
    assert resp.status_code == 200, resp.text
    assert "swagger-ui" in resp.text or "Swagger UI" in resp.text


def test_openapi_json_exposed_and_root_absent() -> None:
    resp = TestClient(create_app(make_config())).get("/openapi.json")
    assert resp.status_code == 200, resp.text
    schema = resp.json()
    assert "openapi" in schema
    # AC-4：跳转端点 include_in_schema=False，不落 openapi paths
    assert "/" not in schema["paths"]
