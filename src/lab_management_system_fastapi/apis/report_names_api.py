# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from lab_management_system_fastapi.apis.report_names_api_base import BaseReportNamesApi
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
from pydantic import StrictInt, StrictStr
from typing import Any, Optional
from lab_management_system_fastapi.models.create_inspection_report_name_request import CreateInspectionReportNameRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.inspection_report_name import InspectionReportName
from lab_management_system_fastapi.models.inspection_standard_role import InspectionStandardRole
from lab_management_system_fastapi.models.object_report_name_link import ObjectReportNameLink
from lab_management_system_fastapi.models.report_name_parameter_link import ReportNameParameterLink
from lab_management_system_fastapi.models.report_name_standard_link import ReportNameStandardLink
from lab_management_system_fastapi.models.report_names_list_object_report_name_links200_response import ReportNamesListObjectReportNameLinks200Response
from lab_management_system_fastapi.models.report_names_list_report_name_parameter_links200_response import ReportNamesListReportNameParameterLinks200Response
from lab_management_system_fastapi.models.report_names_list_report_name_standard_links200_response import ReportNamesListReportNameStandardLinks200Response
from lab_management_system_fastapi.models.report_names_list_report_names200_response import ReportNamesListReportNames200Response
from lab_management_system_fastapi.models.report_names_unlink_object_report_name_request import ReportNamesUnlinkObjectReportNameRequest
from lab_management_system_fastapi.models.report_names_unlink_report_name_parameter_request import ReportNamesUnlinkReportNameParameterRequest
from lab_management_system_fastapi.models.report_names_unlink_report_name_standard_request import ReportNamesUnlinkReportNameStandardRequest
from lab_management_system_fastapi.models.update_inspection_report_name_request import UpdateInspectionReportNameRequest


router = APIRouter()

ns_pkg = lab_management_system_fastapi.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/report-names",
    responses={
        200: {"model": ReportNamesListReportNames200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["report-names"],
    response_model_by_alias=True,
)
async def report_names_list_report_names(
    page: Optional[StrictInt] = Query(None, description="", alias="page"),
    page_size: Optional[StrictInt] = Query(None, description="", alias="pageSize"),
    keyword: Optional[StrictStr] = Query(None, description="", alias="keyword"),
) -> ReportNamesListReportNames200Response:
    if not BaseReportNamesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReportNamesApi.subclasses[0]().report_names_list_report_names(page, page_size, keyword)


@router.post(
    "/api/report-names",
    responses={
        200: {"model": InspectionReportName, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["report-names"],
    response_model_by_alias=True,
)
async def report_names_create_report_name(
    create_inspection_report_name_request: CreateInspectionReportNameRequest = Body(None, description=""),
) -> InspectionReportName:
    if not BaseReportNamesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReportNamesApi.subclasses[0]().report_names_create_report_name(create_inspection_report_name_request)


@router.get(
    "/api/report-names/links/object",
    responses={
        200: {"model": ReportNamesListObjectReportNameLinks200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["report-names"],
    response_model_by_alias=True,
)
async def report_names_list_object_report_name_links(
    inspection_object_code: Optional[StrictStr] = Query(None, description="", alias="inspectionObjectCode"),
    report_name_code: Optional[StrictStr] = Query(None, description="", alias="reportNameCode"),
) -> ReportNamesListObjectReportNameLinks200Response:
    if not BaseReportNamesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReportNamesApi.subclasses[0]().report_names_list_object_report_name_links(inspection_object_code, report_name_code)


@router.post(
    "/api/report-names/links/object",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["report-names"],
    response_model_by_alias=True,
)
async def report_names_link_object_report_name(
    object_report_name_link: ObjectReportNameLink = Body(None, description=""),
) -> None:
    if not BaseReportNamesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReportNamesApi.subclasses[0]().report_names_link_object_report_name(object_report_name_link)


@router.delete(
    "/api/report-names/links/object",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["report-names"],
    response_model_by_alias=True,
)
async def report_names_unlink_object_report_name(
    report_names_unlink_object_report_name_request: ReportNamesUnlinkObjectReportNameRequest = Body(None, description=""),
) -> None:
    if not BaseReportNamesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReportNamesApi.subclasses[0]().report_names_unlink_object_report_name(report_names_unlink_object_report_name_request)


@router.get(
    "/api/report-names/links/parameter",
    responses={
        200: {"model": ReportNamesListReportNameParameterLinks200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["report-names"],
    response_model_by_alias=True,
)
async def report_names_list_report_name_parameter_links(
    report_name_code: Optional[StrictStr] = Query(None, description="", alias="reportNameCode"),
    inspection_parameter_code: Optional[StrictStr] = Query(None, description="", alias="inspectionParameterCode"),
) -> ReportNamesListReportNameParameterLinks200Response:
    if not BaseReportNamesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReportNamesApi.subclasses[0]().report_names_list_report_name_parameter_links(report_name_code, inspection_parameter_code)


@router.post(
    "/api/report-names/links/parameter",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["report-names"],
    response_model_by_alias=True,
)
async def report_names_link_report_name_parameter(
    report_name_parameter_link: ReportNameParameterLink = Body(None, description=""),
) -> None:
    if not BaseReportNamesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReportNamesApi.subclasses[0]().report_names_link_report_name_parameter(report_name_parameter_link)


@router.delete(
    "/api/report-names/links/parameter",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["report-names"],
    response_model_by_alias=True,
)
async def report_names_unlink_report_name_parameter(
    report_names_unlink_report_name_parameter_request: ReportNamesUnlinkReportNameParameterRequest = Body(None, description=""),
) -> None:
    if not BaseReportNamesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReportNamesApi.subclasses[0]().report_names_unlink_report_name_parameter(report_names_unlink_report_name_parameter_request)


@router.get(
    "/api/report-names/links/standard",
    responses={
        200: {"model": ReportNamesListReportNameStandardLinks200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["report-names"],
    response_model_by_alias=True,
)
async def report_names_list_report_name_standard_links(
    report_name_code: Optional[StrictStr] = Query(None, description="", alias="reportNameCode"),
    role: Optional[InspectionStandardRole] = Query(None, description="", alias="role"),
) -> ReportNamesListReportNameStandardLinks200Response:
    if not BaseReportNamesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReportNamesApi.subclasses[0]().report_names_list_report_name_standard_links(report_name_code, role)


@router.post(
    "/api/report-names/links/standard",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["report-names"],
    response_model_by_alias=True,
)
async def report_names_link_report_name_standard(
    report_name_standard_link: ReportNameStandardLink = Body(None, description=""),
) -> None:
    if not BaseReportNamesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReportNamesApi.subclasses[0]().report_names_link_report_name_standard(report_name_standard_link)


@router.delete(
    "/api/report-names/links/standard",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["report-names"],
    response_model_by_alias=True,
)
async def report_names_unlink_report_name_standard(
    report_names_unlink_report_name_standard_request: ReportNamesUnlinkReportNameStandardRequest = Body(None, description=""),
) -> None:
    if not BaseReportNamesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReportNamesApi.subclasses[0]().report_names_unlink_report_name_standard(report_names_unlink_report_name_standard_request)


@router.get(
    "/api/report-names/{code}",
    responses={
        200: {"model": InspectionReportName, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["report-names"],
    response_model_by_alias=True,
)
async def report_names_get_report_name(
    code: StrictStr = Path(..., description=""),
) -> InspectionReportName:
    if not BaseReportNamesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReportNamesApi.subclasses[0]().report_names_get_report_name(code)


@router.put(
    "/api/report-names/{code}",
    responses={
        200: {"model": InspectionReportName, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["report-names"],
    response_model_by_alias=True,
)
async def report_names_update_report_name(
    code: StrictStr = Path(..., description=""),
    update_inspection_report_name_request: UpdateInspectionReportNameRequest = Body(None, description=""),
) -> InspectionReportName:
    if not BaseReportNamesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReportNamesApi.subclasses[0]().report_names_update_report_name(code, update_inspection_report_name_request)


@router.delete(
    "/api/report-names/{code}",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["report-names"],
    response_model_by_alias=True,
)
async def report_names_delete_report_name(
    code: StrictStr = Path(..., description=""),
) -> None:
    if not BaseReportNamesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReportNamesApi.subclasses[0]().report_names_delete_report_name(code)
