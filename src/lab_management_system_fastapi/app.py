"""组合根 —— 手写（生成器 main.py 的手写替代，禁改生成区）。

职责只有装配：把 shared 契约生成的 router 挂上 FastAPI 实例。
业务实现在 impl/；鉴权依赖注入等横切面也在此接线。
"""

from fastapi import FastAPI

from lab_management_system_fastapi.apis.auth_api import router as auth_api_router
from lab_management_system_fastapi.apis.calculation_methods_api import (
    router as calculation_methods_api_router,
)
from lab_management_system_fastapi.apis.contracts_api import router as contracts_api_router
from lab_management_system_fastapi.apis.frontend_bind_meta_api import (
    router as frontend_bind_meta_api_router,
)
from lab_management_system_fastapi.apis.inspection_catalog_api import (
    router as inspection_catalog_api_router,
)
from lab_management_system_fastapi.apis.inspection_dictionary_api import (
    router as inspection_dictionary_api_router,
)
from lab_management_system_fastapi.apis.param_interfaces_api import (
    router as param_interfaces_api_router,
)
from lab_management_system_fastapi.apis.receipts_api import router as receipts_api_router
from lab_management_system_fastapi.apis.report_names_api import router as report_names_api_router
from lab_management_system_fastapi.apis.samples_api import router as samples_api_router
from lab_management_system_fastapi.apis.summary_api import router as summary_api_router
from lab_management_system_fastapi.apis.technical_requirements_api import (
    router as technical_requirements_api_router,
)
from lab_management_system_fastapi.apis.test_records_api import router as test_records_api_router

app = FastAPI(
    title="实验室管理系统",
    version="0.1.0",
)

_ROUTERS = (
    auth_api_router,
    calculation_methods_api_router,
    contracts_api_router,
    frontend_bind_meta_api_router,
    inspection_catalog_api_router,
    inspection_dictionary_api_router,
    param_interfaces_api_router,
    receipts_api_router,
    report_names_api_router,
    samples_api_router,
    summary_api_router,
    technical_requirements_api_router,
    test_records_api_router,
)

for _router in _ROUTERS:
    app.include_router(_router)
