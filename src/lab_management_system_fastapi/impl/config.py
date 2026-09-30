"""应用配置 —— env fail-fast，无默认值兜底（suite 硬规则 §1；ADR-0019 同款口径）。

env 键面镜像 lab-springboot application.yml ``lab:`` 段（REQ-2026-002 T-2）：
JWT 四键 + LAB_SSO/LAB_AUTH 十键 + DATABASE_URL。唯一非 fail-fast 的键是
``LAB_SSO_LOGIN_URL``：空回落 saas base 是家族语义（springboot
``LabConfig.Sso.effectiveLoginUrl`` 的 javadoc——dev 时 saas-nextjs 同源），
不是 env 缺省兜底。
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _require_env(key: str) -> str:
    value = os.environ.get(key)
    if value is None or value == "":
        raise RuntimeError(f"env {key} required（禁默认值兜底，suite 硬规则 §1）")
    return value


def normalize_database_url(url: str) -> str:
    """家族 DATABASE_URL 方言归一：剥 ``jdbc:`` 前缀，``postgresql://`` → ``+psycopg2``。

    与 scaffold-entities.sh 同一套归一规则（sqlacodegen 4.x 默认 psycopg3，须显式指回）。
    """
    value = url[len("jdbc:") :] if url.startswith("jdbc:") else url
    if value.startswith("postgresql://"):
        value = "postgresql+psycopg2://" + value[len("postgresql://") :]
    return value


@dataclass(frozen=True)
class AppConfig:
    database_url: str
    jwt_signing_key: str
    jwt_issuer: str
    jwt_ttl_seconds: int
    jwt_refresh_ttl_seconds: int
    saas_base_url: str
    sso_login_url: str
    saas_client_id: str
    saas_client_secret: str
    saas_default_tenant_id: str
    sso_callback_redirect: str
    saas_service_user: str
    saas_service_password: str
    saas_service_client_id: str
    auth_dev_password: str
    cors_allowed_origins: str

    @property
    def effective_login_url(self) -> str:
        """saas IdP 登录页 base：``{loginUrl}/login?...``；空回落 saas base（家族语义，
        见模块 docstring）。"""
        return self.sso_login_url if self.sso_login_url.strip() else self.saas_base_url

    @property
    def cors_origins(self) -> list[str]:
        """CSV 白名单 → 列表（springboot SecurityConfig.corsConfigurationSource
        逐条 trim 镜像）。"""
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @classmethod
    def from_env(cls) -> AppConfig:
        return cls(
            database_url=_require_env("DATABASE_URL"),
            jwt_signing_key=_require_env("JWT_SIGNING_KEY"),
            jwt_issuer=_require_env("JWT_ISSUER"),
            jwt_ttl_seconds=int(_require_env("JWT_TTL_SECONDS")),
            jwt_refresh_ttl_seconds=int(_require_env("JWT_REFRESH_TTL_SECONDS")),
            saas_base_url=_require_env("LAB_SAAS_BASE_URL"),
            sso_login_url=os.environ.get("LAB_SSO_LOGIN_URL", ""),
            saas_client_id=_require_env("LAB_SAAS_CLIENT_ID"),
            saas_client_secret=_require_env("LAB_SAAS_CLIENT_SECRET"),
            saas_default_tenant_id=_require_env("LAB_SAAS_DEFAULT_TENANT_ID"),
            sso_callback_redirect=_require_env("LAB_SSO_CALLBACK_REDIRECT"),
            saas_service_user=_require_env("LAB_SAAS_SERVICE_USER"),
            saas_service_password=_require_env("LAB_SAAS_SERVICE_PASSWORD"),
            saas_service_client_id=_require_env("LAB_SAAS_SERVICE_CLIENT_ID"),
            auth_dev_password=_require_env("LAB_AUTH_DEV_PASSWORD"),
            cors_allowed_origins=_require_env("LAB_CORS_ALLOWED_ORIGINS"),
        )
