"""pytest 适配器：@pytest.mark.fn -> suite 契约的 .state/trace.json。

批2（REQ-2026-003）增补：L4 打 PG 真库 scratch 库 ``lab_fastapi_scratch``
（镜像 saas fastapi conftest 配方：DROP→CREATE→create_all→收工 DROP，
fail-fast 在 fixture 内不在 import 期——trace collect-only 不碰 env）。
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy import insert as sa_insert
from sqlalchemy.engine import Engine, make_url

from lab_management_system_fastapi.app import create_app
from lab_management_system_fastapi.entities import (
    Base,
    InspectionCalculationMethods,
    InspectionGrades,
    InspectionObjectParameters,
    InspectionObjectReportNames,
    InspectionObjects,
    InspectionObjectStandards,
    InspectionParameters,
    InspectionParamInterfaceLinks,
    InspectionParamInterfaces,
    InspectionReportNameParameters,
    InspectionReportNames,
    InspectionReportNameStandards,
    InspectionSpecialties,
    InspectionSpecialtyObjects,
    InspectionStandardParameters,
    InspectionStandards,
    InspectionTechnicalRequirements,
)
from lab_management_system_fastapi.impl.config import AppConfig, normalize_database_url


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "fn(id, ...): 该测试验证的功能子项 ID，如 @pytest.mark.fn('M06.F01.I01')"
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """trace 适配器（saas 仓同款）：TRACE_MAP=1 时把 fn marker 映射写 trace.json——
    suite 契约二唯一产出通道（harness.load_trace 只跑 trace_cmd，写入靠本钩子）。"""
    if os.environ.get("TRACE_MAP") != "1":
        return
    entries = []
    for item in items:
        fns: list[str] = []
        for marker in item.iter_markers(name="fn"):
            fns.extend(str(a) for a in marker.args)
        inert = any(item.get_closest_marker(n) is not None for n in ("skip", "skipif", "xfail"))
        entries.append(
            {"test": item.nodeid, "fns": [] if inert else sorted(set(fns)), "inert": inert}
        )
    out = Path(str(config.rootpath)) / ".state" / "trace.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"schema": 1, "tests": entries}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


SCRATCH_DB = "lab_fastapi_scratch"

# 家族 dev 签名密钥（九仓共享 dev-key-32-bytes-minimum-length!，LabJwtSigner javadoc 参照）
TEST_KEY = "dev-key-32-bytes-minimum-length!"
ISSUER = "lab-management-fastapi"
DEV_PASSWORD = "dev123456"

_T = "2026-09-30T08:00:00+00:00"

# 种子键（跨测试文件共享；业务单测走 login(alice) → tenant claim 缺省 = directory 默认租户）
SP1, SP2 = "SP-01", "SP-02"
OBJ1, OBJ2 = "OBJ-01", "OBJ-02"
PAR_A, PAR_B, PAR_C = "PAR-A", "PAR-B", "PAR-C"
STD1, STD2, STD3 = "STD-1", "STD-2", "STD-3"
RN1, RN2 = "RN-01", "RN-02"
PI1, PI2 = "PI-1", "PI-2"


def make_config() -> AppConfig:
    return AppConfig(
        database_url="postgresql://lab:pw@localhost:5432/lab_unused_tests",
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


def _sql_exec(engine: Engine, statement: str) -> None:
    """DDL 专用（CREATE/DROP DATABASE 不能进事务块）：AUTOCOMMIT 直发。"""
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text(statement))


def _scratch_urls() -> tuple[object, object]:
    """fail-fast 在 fixture 内而非 import 期：pytest 收集（trace collect-only）不碰 env。"""
    raw = os.environ.get("DATABASE_URL")
    if raw is None or raw == "":
        raise RuntimeError(
            "env DATABASE_URL required —— L4 打 PG 真库（scratch 库与其同服务器）；"
            "gate 表驱动注入 lab_test URL（L4_DB_INJECT_REPOS，2026-09-30 人裁），"
            "手工跑先显式 export（suite 硬规则 §1）"
        )
    server = make_url(normalize_database_url(raw))
    # scratch 与测试库同服务器：借 DATABASE_URL 的 host/凭据，库名换成 scratch
    return server.set(database="postgres"), server.set(database=SCRATCH_DB)


@pytest.fixture(scope="session")
def scratch_engine() -> Iterator[Engine]:
    """每轮测试独占 scratch 库：DROP→CREATE→真实 schema create_all→收工 DROP。

    WITH (FORCE) 兜底上次异常退出残留的连接（PG 13+）。
    """
    admin_url, scratch_url = _scratch_urls()  # fail-fast：无 DATABASE_URL 即红
    admin = create_engine(admin_url)
    _sql_exec(admin, f'DROP DATABASE IF EXISTS "{SCRATCH_DB}" WITH (FORCE)')
    _sql_exec(admin, f'CREATE DATABASE "{SCRATCH_DB}"')
    engine = create_engine(scratch_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()
    _sql_exec(admin, f'DROP DATABASE "{SCRATCH_DB}" WITH (FORCE)')
    admin.dispose()


def _seed(conn: Any) -> None:
    """M06 字典种子（镜像 lab-msw 家族 dev 数据形状；平台级字典 + tech_req 双租户行）。"""
    rows: dict[Any, list[dict[str, Any]]] = {
        InspectionSpecialties: [
            {
                "code": SP1,
                "official_no": "OF-01",
                "name": "混凝土结构检测",
                "is_official": True,
                "enabled": True,
                "sort_order": 2,
                "created_at": _T,
                "updated_at": _T,
            },
            {
                "code": SP2,
                "official_no": "OF-02",
                "name": "安全防护检测",
                "is_official": True,
                "enabled": True,
                "sort_order": 1,
                "created_at": _T,
                "updated_at": _T,
            },
        ],
        InspectionObjects: [
            {
                "code": OBJ1,
                "inspection_specialty_code": SP1,
                "source_project_no": "P-2026-001",
                "source_project_name": "市住建质量年检",
                "name": "混凝土抗压强度检测",
                "is_optional_for_qualification": False,
                "is_official": True,
                "enabled": True,
                "sort_order": 1,
                "created_at": _T,
                "updated_at": _T,
            },
            {
                "code": OBJ2,
                "inspection_specialty_code": SP2,
                "source_project_no": "P-2026-002",
                "source_project_name": "工地安全普查",
                "name": "锚杆抗拔承载力检测",
                "is_optional_for_qualification": True,
                "is_official": True,
                "enabled": True,
                "sort_order": 2,
                "created_at": _T,
                "updated_at": _T,
            },
        ],
        InspectionParameters: [
            {
                "code": PAR_A,
                "name": "抗压强度",
                "raw_name": "抗压强度",
                "canonical_name": "抗压强度",
                "aliases": ["立方体抗压"],
                "source_type": "official",
                "sort_order": 1,
                "created_at": _T,
                "updated_at": _T,
            },
            {
                "code": PAR_B,
                "name": "抗拔承载力",
                "raw_name": "抗拔力",
                "canonical_name": "抗拔承载力",
                "aliases": [],
                "source_type": "official",
                "sort_order": 2,
                "created_at": _T,
                "updated_at": _T,
            },
            {
                "code": PAR_C,
                "name": "挠度",
                "raw_name": "挠度",
                "canonical_name": "挠度",
                "aliases": [],
                "source_type": "custom",
                "sort_order": 3,
                "created_at": _T,
                "updated_at": _T,
            },
        ],
        InspectionStandards: [
            {
                "code": STD1,
                "name": "混凝土物理力学性能试验方法标准",
                "version": "2024",
                "status": "active",
                "source_document_id": None,
                "source_hash": None,
                "sort_order": 1,
                "created_at": _T,
                "updated_at": _T,
            },
            {
                "code": STD2,
                "name": "回弹法检测抗压强度（旧版被替代）",
                "version": "2015",
                "status": "superseded",
                "source_document_id": None,
                "source_hash": None,
                "sort_order": 2,
                "created_at": _T,
                "updated_at": _T,
            },
            {
                "code": STD3,
                "name": "工程测量规范（草案）",
                "version": "2026",
                "status": "draft",
                "source_document_id": None,
                "source_hash": None,
                "sort_order": 3,
                "created_at": _T,
                "updated_at": _T,
            },
        ],
        # 先父后子（FK 顺序）：calc/tech_req 引用 report_names；junction 引用全体
        InspectionReportNames: [
            {
                "code": RN1,
                "name": "混凝土抗压强度检测报告",
                "full_name": "检测报告（2026）抗字第0001号",
                "template_path": "templates/compression.docx",
                "summary_name": "抗压汇总",
                "ext_fields": [
                    {
                        "key": "castDate",
                        "label": "浇筑日期",
                        "type": "date",
                        "required": True,
                        "options": None,
                        "tag": None,
                        "source": "sample",
                    },
                    {
                        "key": "strength",
                        "label": "强度等级",
                        "type": "select",
                        "required": True,
                        "options": ["C25", "C30", "C35"],
                        "tag": None,
                        "source": None,
                    },
                ],
                "description": None,
                "sort_order": 1,
                "created_at": _T,
                "updated_at": _T,
            },
            {
                "code": RN2,
                "name": "锚杆抗拔检测报告",
                "full_name": None,
                "template_path": None,
                "summary_name": None,
                "ext_fields": [],
                "description": None,
                "sort_order": 2,
                "created_at": _T,
                "updated_at": _T,
            },
        ],
        InspectionParamInterfaces: [
            {
                "code": PI1,
                "component_path": "views/records/CompressionForm",
                "sort_order": 1,
                "created_at": _T,
                "updated_at": _T,
                "name": "抗压数据录入界面",
                "description": None,
                "is_official": True,
                "config": {"columns": 3, "grid": True},
            },
            {
                "code": PI2,
                "component_path": "views/records/AnchorForm",
                "sort_order": 2,
                "created_at": _T,
                "updated_at": _T,
                "name": "抗拔数据录入界面",
                "description": None,
                "is_official": False,
                "config": None,
            },
        ],
        # tech_req.grade → inspection_grades FK：补批3 catalog 形状的最小种子
        # （grades PK=code、unique(tenant_id,code)、FK object SET NULL；本批只种 grades，
        # brand/model/spec 同构待批3 实批）
        InspectionGrades: [
            {
                "code": "C30",
                "name": "C30",
                "sort_order": 1,
                "tenant_id": "",
                "inspection_object_code": OBJ1,
                "remark": None,
                "created_at": _T,
                "updated_at": _T,
            },
            {
                "code": "C25",
                "name": "C25",
                "sort_order": 2,
                "tenant_id": "",
                "inspection_object_code": OBJ1,
                "remark": None,
                "created_at": _T,
                "updated_at": _T,
            },
        ],
        InspectionCalculationMethods: [
            {
                "inspection_object_code": OBJ1,
                "inspection_parameter_code": PAR_A,
                "testing_standard_code": STD1,
                "report_name_code": RN1,
                "algorithm_type": "manual",
                "specimen_count": 1,
                "formula": "R = P/A",
                "conditions": "标准养护 28d",
                "rounding_rule": "0.1",
                "remark": None,
                "sort_order": 1,
                "created_at": _T,
                "updated_at": _T,
            },
        ],
        InspectionTechnicalRequirements: [
            # 双租户异三键行（PG PK=三键，同三键跨租户不可并存——schema 事实，
            # springboot TechnicalRequirementKey 四部件在 PG 侧不可表达）：
            # TENANT-001 verified min30 @ PAR-A / TENANT-002 draft min25 @ PAR-B
            {
                "inspection_object_code": OBJ1,
                "inspection_parameter_code": PAR_A,
                "judgment_standard_code": STD1,
                "value_type": "numeric",
                "comparison": "≥",
                "judgment_mode": "manual",
                "verification_status": "verified",
                "tenant_id": "TENANT-001",
                "conditions": None,
                "min_value": 30,
                "max_value": None,
                "target_value": None,
                "expression": None,
                "unit": "MPa",
                "clause": "6.3.1",
                "source_page": 7,
                "source_hash": "h1",
                "brand": None,
                "model": None,
                "grade": "C30",
                "spec": None,
                "sieve": None,
                "remark": None,
                "sort_order": 1,
                "created_at": _T,
                "updated_at": _T,
            },
            {
                "inspection_object_code": OBJ1,
                "inspection_parameter_code": PAR_B,
                "judgment_standard_code": STD1,
                "value_type": "numeric",
                "comparison": "≥",
                "judgment_mode": "manual",
                "verification_status": "draft",
                "tenant_id": "TENANT-002",
                "conditions": None,
                "min_value": 25,
                "max_value": None,
                "target_value": None,
                "expression": None,
                "unit": "MPa",
                "clause": None,
                "source_page": None,
                "source_hash": None,
                "brand": None,
                "model": None,
                "grade": "C25",
                "spec": None,
                "sieve": None,
                "remark": None,
                "sort_order": 1,
                "created_at": _T,
                "updated_at": _T,
            },
        ],
        # junction 种子：8 家族各 1-2 行（覆盖 list 过滤与 unlink 幂等基线）
        InspectionSpecialtyObjects: [
            {
                "inspection_specialty_code": SP1,
                "inspection_object_code": OBJ1,
                "remark": "主项",
                "created_at": _T,
                "updated_at": _T,
            },
        ],
        InspectionObjectParameters: [
            {
                "inspection_object_code": OBJ1,
                "inspection_parameter_code": PAR_A,
                "qualification_level": "QUALIFIED",
                "source_page": 7,
                "remark": "主参数",
                "created_at": _T,
                "updated_at": _T,
            },
        ],
        InspectionObjectStandards: [
            {
                "inspection_object_code": OBJ1,
                "inspection_standard_code": STD1,
                "role": "JUDGMENT",
                "remark": None,
                "created_at": _T,
                "updated_at": _T,
            },
        ],
        InspectionStandardParameters: [
            {
                "inspection_standard_code": STD1,
                "inspection_parameter_code": PAR_A,
                "created_at": _T,
                "updated_at": _T,
            },
        ],
        InspectionObjectReportNames: [
            {
                "inspection_object_code": OBJ1,
                "report_name_code": RN1,
                "remark": None,
                "created_at": _T,
                "updated_at": _T,
            },
        ],
        InspectionReportNameParameters: [
            {
                "report_name_code": RN1,
                "inspection_parameter_code": PAR_A,
                "remark": None,
                "created_at": _T,
                "updated_at": _T,
            },
        ],
        InspectionReportNameStandards: [
            {
                "report_name_code": RN1,
                "inspection_standard_code": STD1,
                "role": "JUDGMENT",
                "remark": "判据",
                "created_at": _T,
                "updated_at": _T,
            },
        ],
        InspectionParamInterfaceLinks: [
            {
                "inspection_parameter_code": PAR_A,
                "param_interface_code": PI1,
                "report_name_code": RN1,
                "config": {"mode": "auto"},
                "created_at": _T,
                "updated_at": _T,
            },
        ],
    }
    for table, table_rows in rows.items():
        conn.execute(sa_insert(table).values(table_rows))


def _truncate_all(engine: Engine) -> None:
    tables = ", ".join(f'"{t}"' for t in sorted(Base.metadata.tables))
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture()
def db_client(scratch_engine: Engine) -> Iterator[TestClient]:
    """每测试独占数据：TRUNCATE → 种子 → create_app(engine 注入) → ASGI 直连。

    saas 簇 fake 注入 app.state 缝（login 链路拉菜单快照用；SSO 真连归批6 live）。
    """
    from tests.test_auth_batch1 import FakeSaasAuth, FakeSaasMe

    _truncate_all(scratch_engine)
    with scratch_engine.begin() as conn:
        _seed(conn)
    app = create_app(make_config(), engine=scratch_engine)
    app.state.saas_auth = FakeSaasAuth()
    app.state.saas_me = FakeSaasMe()
    client = TestClient(app)
    yield client
    client.close()


@pytest.fixture()
def bearer(db_client: TestClient) -> str:
    """登录 alice 换 Bearer token（密码登录链路：directory + fake saas 菜单快照）。"""
    resp = db_client.post("/api/auth/login", json={"username": "alice", "password": "dev123456"})
    assert resp.status_code == 200, resp.text
    token: str = resp.json()["token"]
    return token
