"""菜单/成员资格快照缓存 + saas 菜单树映射 —— lab-springboot MenuSnapshotCache /
MembershipSnapshotCache / SaasMenuMapper 镜像（REQ-2026-002 T-3）。

局限同 springboot（javadoc）：进程内缓存多实例不共享；TTL 30min 后需 refresh 或
重登重新填充。菜单变更生效时延 = min(refresh 周期, TTL)。
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from lab_management_system_fastapi.impl.saas_client import SaasMenuNode
from lab_management_system_fastapi.models.menu_node import MenuNode
from lab_management_system_fastapi.models.my_tenant import MyTenant

_TTL = timedelta(minutes=30)

# group 类型节点缺省 icon（与静态 demo 菜单 icon 风格对齐，SaasMenuMapper 常量镜像）
DEFAULT_GROUP_ICON = "resource"
DEFAULT_PAGE_ICON = "file"


def _now() -> datetime:
    return datetime.now(UTC)


def _sorted_by_sort_order(nodes: list[SaasMenuNode]) -> list[SaasMenuNode]:
    """sortOrder 升序、None 置尾（nullsLast 镜像）。"""
    return sorted(nodes, key=lambda n: (n.sort_order is None, n.sort_order or 0))


def map_saas_menus(roots: list[SaasMenuNode]) -> list[MenuNode]:
    """saas EffectiveMenuNode → lab 契约 MenuNode 递归映射（SaasMenuMapper 镜像）。

    label = title ?? code（saas 名称字段是 title，见 saas_client.SaasMenuNode 注）；
    icon = icon ?? (group→"resource"、page→"file")；子树防御性再排一次。
    """
    return [_map_node(node) for node in _sorted_by_sort_order(roots)]


def _map_node(src: SaasMenuNode) -> MenuNode:
    icon = src.icon
    if not icon:
        icon = DEFAULT_GROUP_ICON if src.type == "group" else DEFAULT_PAGE_ICON
    children = [_map_node(child) for child in _sorted_by_sort_order(src.children)]
    return MenuNode(
        id=src.id,
        label=src.title if src.title else src.code if src.code else src.id,
        path=src.path,
        icon=icon,
        children=children or None,
    )


class MenuSnapshotCache:
    """per-user 已映射菜单树快照（miss → /menus 503 MENUS_UNAVAILABLE，demo 兜底已删口径）。"""

    def __init__(self, ttl: timedelta = _TTL) -> None:
        self._ttl = ttl
        self._snapshots: dict[str, tuple[list[MenuNode], datetime]] = {}

    def put(self, user_id: str, menus: list[MenuNode]) -> None:
        self._snapshots[user_id] = (list(menus), _now() + self._ttl)

    def get(self, user_id: str | None) -> list[MenuNode] | None:
        if user_id is None:
            return None
        entry = self._snapshots.get(user_id)
        if entry is None:
            return None
        menus, expires_at = entry
        if expires_at < _now():
            del self._snapshots[user_id]
            return None
        return menus


class MembershipSnapshotCache:
    """per-user saas memberships 快照（me() 对 SSO 用户必读；miss → 401 refresh 自愈）。"""

    def __init__(self, ttl: timedelta = _TTL) -> None:
        self._ttl = ttl
        self._snapshots: dict[str, tuple[list[MyTenant], datetime]] = {}

    def put(self, user_id: str, tenants: list[MyTenant]) -> None:
        self._snapshots[user_id] = (list(tenants), _now() + self._ttl)

    def get(self, user_id: str | None) -> list[MyTenant] | None:
        if user_id is None:
            return None
        entry = self._snapshots.get(user_id)
        if entry is None:
            return None
        tenants, expires_at = entry
        if expires_at < _now():
            del self._snapshots[user_id]
            return None
        return tenants
