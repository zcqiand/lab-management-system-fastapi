"""家族错误契约：ErrorResponse {code,message}，异常 → HTTP 映射镜像 lab-springboot
GlobalExceptionHandler（REQ-2026-002 T-2）：

- IllegalArgumentException → 400 BAD_REQUEST（本仓 BadRequestError）
- SecurityException / AuthenticationException → 401 INVALID_CREDENTIALS
- NoSuchElementException → 404 NOT_FOUND
- SaasAuthException 按子类分流：InvalidGrant → 400 INVALID_GRANT /
  UnauthorizedClient → 401 INVALID_CREDENTIALS / 其余 → 502 SAAS_UPSTREAM_ERROR
- MenusUnavailableException → 503 MENUS_UNAVAILABLE
"""

from __future__ import annotations


class ApiError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class BadRequestError(ApiError):
    status_code = 400
    code = "BAD_REQUEST"


class InvalidCredentialsError(ApiError):
    status_code = 401
    code = "INVALID_CREDENTIALS"


class ForbiddenError(ApiError):
    status_code = 403
    code = "FORBIDDEN"


class NotFoundError(ApiError):
    status_code = 404
    code = "NOT_FOUND"


class InvalidGrantError(ApiError):
    """saas 4xx 拒绝（code 重放/过期，RFC 6749 §5.2 invalid_grant）→ 400。"""

    status_code = 400
    code = "INVALID_GRANT"


class UnauthorizedClientError(ApiError):
    """saas 401（client 凭据不被认）→ 401 INVALID_CREDENTIALS（家族映射）。"""

    status_code = 401
    code = "INVALID_CREDENTIALS"


class SaasUpstreamError(ApiError):
    """saas 5xx / 连接失败 → 502（CF 会把 5xx 换皮，detail 走 body 留痕）。"""

    status_code = 502
    code = "SAAS_UPSTREAM_ERROR"


class MenusUnavailableError(ApiError):
    """菜单快照 miss（重启/TTL 过期/拉取失败）→ 503 可恢复临时态，前端回退静态菜单。"""

    status_code = 503
    code = "MENUS_UNAVAILABLE"
