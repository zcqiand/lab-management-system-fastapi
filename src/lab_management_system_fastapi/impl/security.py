"""JWT 签发/校验 + Bearer 提取 —— lab-springboot LabJwtSigner 镜像（REQ-2026-002 T-2）。

- HS256，JWT_SIGNING_KEY ≥32 字节；claims iss/sub/tenant_id?/typ/iat/exp
  （lab JWT **无 aud/jti/nbf** —— 与 saas 仓 JwtIssuer 的差异点，验签侧 verify_aud=False）
- refresh token typ=refresh，内嵌 saas_refresh_token claim（lab 无状态不持 saas 会话）
- PyJWT encode 默认 sort_keys → 与 springboot TreeMap 字典序 payload 一致；
  header 固定 {"alg":"HS256","typ":"JWT"} 同款
"""

from __future__ import annotations

from datetime import UTC, datetime

import jwt

from lab_management_system_fastapi.impl.config import AppConfig
from lab_management_system_fastapi.impl.context import RequestContext
from lab_management_system_fastapi.impl.errors import BadRequestError, InvalidCredentialsError


def now_utc() -> datetime:
    return datetime.now(UTC)


def _epoch() -> int:
    return int(datetime.now(UTC).timestamp())


class JwtIssuer:
    def __init__(self, config: AppConfig) -> None:
        if len(config.jwt_signing_key.encode()) < 32:
            raise RuntimeError("JWT_SIGNING_KEY must be >=32 bytes for HS256")
        self._key = config.jwt_signing_key
        self._issuer = config.jwt_issuer
        self._access_ttl = config.jwt_ttl_seconds
        self._refresh_ttl = config.jwt_refresh_ttl_seconds

    def issue(self, user_id: str, tenant_id: str | None) -> str:
        """签 access token；tenantId 可空（无选租户时不带 claim，LabJwtSigner.issue 镜像）。"""
        now = _epoch()
        payload: dict[str, object] = {
            "sub": user_id,
            "iat": now,
            "exp": now + self._access_ttl,
            "typ": "access",
            "iss": self._issuer,
        }
        if tenant_id:
            payload["tenant_id"] = tenant_id
        return str(jwt.encode(payload, self._key, algorithm="HS256"))

    def issue_refresh(self, user_id: str, saas_refresh_token: str) -> str:
        """签 refresh token，载荷内嵌 saas refresh token；空值 400
        （springboot IllegalArgument 镜像）。"""
        if not saas_refresh_token:
            raise BadRequestError("saasRefreshToken required for refresh token")
        now = _epoch()
        payload: dict[str, object] = {
            "sub": user_id,
            "saas_refresh_token": saas_refresh_token,
            "iat": now,
            "exp": now + self._refresh_ttl,
            "typ": "refresh",
            "iss": self._issuer,
        }
        return str(jwt.encode(payload, self._key, algorithm="HS256"))

    def verify(self, token: str) -> dict[str, object]:
        """验签 + iss + exp（PyJWT 默认含 exp 校验）；失败 401（调用方 refresh 路径再加前缀）。"""
        if not token:
            raise InvalidCredentialsError("token is empty")
        try:
            claims: dict[str, object] = jwt.decode(
                token,
                key=self._key,
                algorithms=["HS256"],
                issuer=self._issuer,
                options={"verify_aud": False},
            )
        except jwt.PyJWTError as exc:
            raise InvalidCredentialsError(str(exc)) from exc
        return claims


def require_bearer(ctx: RequestContext, issuer: JwtIssuer) -> dict[str, object]:
    """取当前 Bearer 身份：无/坏 → 401（生成路由无全局鉴权兜底，impl 首行显式挂）。"""
    header = ctx.request.headers.get("Authorization")
    if header is None or not header.startswith("Bearer "):
        raise InvalidCredentialsError("Bearer token required")
    return issuer.verify(header[len("Bearer ") :].strip())
