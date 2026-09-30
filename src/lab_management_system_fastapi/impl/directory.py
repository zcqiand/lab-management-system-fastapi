"""配置式内存用户目录 —— lab-springboot ConfigUserDirectory 1:1 镜像（REQ-2026-002 T-2）。

数据 1:1 镜像 lab-msw（家族 dev 约定）：

- 用户：alice / ``LAB_AUTH_DEV_PASSWORD``（USER-A，roleCode=admin）；dev 凭证与
  saas seed（V016 alice）同源，contract-test 依赖
- 租户：TENANT-001 city-lab / TENANT-002 district-lab / TENANT-003 third-party
- 运行时 upsert：SSO 用户按 email 键落 ``_upserted`` 内存 Map（重启即清，refresh 自愈链兜底）
- per-user saas refresh_token：saas rotate-once 消费即作废，me/menus 缓存 miss
  reload 后必须存回新的（镜像 aspnetcore 同名机制）
"""

from __future__ import annotations

from lab_management_system_fastapi.models.current_user import CurrentUser
from lab_management_system_fastapi.models.my_tenant import MyTenant

_DEMO_USER = CurrentUser(id="USER-A", username="alice", displayName="管理员", roleCode="admin")

_TENANTS: list[MyTenant] = [
    MyTenant(
        tenantId="TENANT-001",
        code="city-lab",
        name="市住建工程质量检测中心",
        roleIds=["admin"],
    ),
    MyTenant(tenantId="TENANT-002", code="district-lab", name="区检测站", roleIds=["technician"]),
    MyTenant(
        tenantId="TENANT-003",
        code="third-party",
        name="第三方检测实验室",
        roleIds=["viewer"],
    ),
]


class ConfigUserDirectory:
    """无身份表的配置式目录（ADR-0008）：查/比/upsert 全内存。"""

    def __init__(self, dev_password: str) -> None:
        if not dev_password:
            raise RuntimeError(
                'LAB_AUTH_DEV_PASSWORD 必填（ADR-0019 禁 "dev123456" 字面默认值，suite 硬规则 §1）'
            )
        self._dev_password = dev_password
        self._upserted: dict[str, CurrentUser] = {}
        self._saas_refresh_tokens: dict[str, str] = {}

    def find_by_username(self, username: str | None) -> CurrentUser | None:
        if username is None:
            return None
        if _DEMO_USER.username == username:
            return _DEMO_USER
        return next((u for u in self._upserted.values() if u.username == username), None)

    def find_by_email(self, email: str | None) -> CurrentUser | None:
        # 镜像 quirk：springboot findByEmail 对 DEMO 用户比对的是 username（非 email 字段）
        if email is None:
            return None
        if email == _DEMO_USER.username:
            return _DEMO_USER
        return next((u for u in self._upserted.values() if u.username == email), None)

    def find_by_id(self, user_id: str | None) -> CurrentUser | None:
        if user_id is None:
            return None
        if _DEMO_USER.id == user_id:
            return _DEMO_USER
        return next((u for u in self._upserted.values() if u.id == user_id), None)

    def check_password(self, username: str, password: str) -> bool:
        return _DEMO_USER.username == username and self._dev_password == password

    def tenants_of(self, _username: str) -> list[MyTenant]:
        # 镜像 springboot UserDirectory 接口形参：demo 目录全体用户租户一致，username 刻意不消费
        return list(_TENANTS)

    def default_tenant(self) -> MyTenant:
        return _TENANTS[0]

    def find_by_tenant_id(self, tenant_id: str) -> MyTenant | None:
        return next((t for t in _TENANTS if t.tenant_id == tenant_id), None)

    def upsert(
        self, user_id: str, email: str, display_name: str | None, role_code: str | None
    ) -> CurrentUser:
        # 优先按 email 找，命中即返回既有（不更新字段，镜像 springboot）；roleCode 空兜 viewer
        existing = self._upserted.get(email)
        if existing is not None:
            return existing
        user = CurrentUser(
            id=user_id,
            username=email,
            displayName=display_name,
            roleCode=role_code if role_code else "viewer",
        )
        self._upserted[email] = user
        return user

    def set_saas_refresh_token(self, user_id: str | None, saas_refresh_token: str | None) -> None:
        if not user_id or not saas_refresh_token:
            return
        self._saas_refresh_tokens[user_id] = saas_refresh_token

    def get_saas_refresh_token(self, user_id: str) -> str | None:
        if not user_id:
            return None
        return self._saas_refresh_tokens.get(user_id)
