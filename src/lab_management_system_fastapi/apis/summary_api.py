# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from lab_management_system_fastapi.apis.summary_api_base import BaseSummaryApi
import lab_management_system_fastapi.impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from lab_management_system_fastapi.models.extra_models import TokenModel  # noqa: F401
from pydantic import StrictStr
from typing import Optional
from lab_management_system_fastapi.models.dashboard_stats import DashboardStats
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.summary_data import SummaryData


router = APIRouter()

ns_pkg = lab_management_system_fastapi.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/summary",
    responses={
        200: {"model": SummaryData, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["summary"],
    response_model_by_alias=True,
)
async def summary_get_report_summary(
    category_code: Optional[StrictStr] = Query(None, description="", alias="categoryCode"),
    date_from: Optional[StrictStr] = Query(None, description="", alias="dateFrom"),
    date_to: Optional[StrictStr] = Query(None, description="", alias="dateTo"),
) -> SummaryData:
    if not BaseSummaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseSummaryApi.subclasses[0]().summary_get_report_summary(category_code, date_from, date_to)


@router.get(
    "/api/summary/stats",
    responses={
        200: {"model": DashboardStats, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["summary"],
    response_model_by_alias=True,
)
async def summary_get_dashboard_stats(
) -> DashboardStats:
    if not BaseSummaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseSummaryApi.subclasses[0]().summary_get_dashboard_stats()
