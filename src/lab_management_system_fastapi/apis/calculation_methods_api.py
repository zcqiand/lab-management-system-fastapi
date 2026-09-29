# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from lab_management_system_fastapi.apis.calculation_methods_api_base import BaseCalculationMethodsApi
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
from typing import Any, List, Optional
from lab_management_system_fastapi.models.calculation_method import CalculationMethod
from lab_management_system_fastapi.models.create_calculation_method_request import CreateCalculationMethodRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.update_calculation_method_request import UpdateCalculationMethodRequest


router = APIRouter()

ns_pkg = lab_management_system_fastapi.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/calculation-methods",
    responses={
        200: {"model": List[CalculationMethod], "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["calculation-methods"],
    response_model_by_alias=True,
)
async def calculation_methods_list_calculation_methods(
    inspection_object_code: Optional[StrictStr] = Query(None, description="", alias="inspectionObjectCode"),
    inspection_parameter_code: Optional[StrictStr] = Query(None, description="", alias="inspectionParameterCode"),
) -> List[CalculationMethod]:
    if not BaseCalculationMethodsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCalculationMethodsApi.subclasses[0]().calculation_methods_list_calculation_methods(inspection_object_code, inspection_parameter_code)


@router.post(
    "/api/calculation-methods",
    responses={
        200: {"model": CalculationMethod, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["calculation-methods"],
    response_model_by_alias=True,
)
async def calculation_methods_create_calculation_method(
    create_calculation_method_request: CreateCalculationMethodRequest = Body(None, description=""),
) -> CalculationMethod:
    if not BaseCalculationMethodsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCalculationMethodsApi.subclasses[0]().calculation_methods_create_calculation_method(create_calculation_method_request)


@router.get(
    "/api/calculation-methods/{inspectionObjectCode}/{inspectionParameterCode}",
    responses={
        200: {"model": CalculationMethod, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["calculation-methods"],
    response_model_by_alias=True,
)
async def calculation_methods_get_calculation_method(
    inspectionObjectCode: StrictStr = Path(..., description=""),
    inspectionParameterCode: StrictStr = Path(..., description=""),
) -> CalculationMethod:
    if not BaseCalculationMethodsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCalculationMethodsApi.subclasses[0]().calculation_methods_get_calculation_method(inspectionObjectCode, inspectionParameterCode)


@router.put(
    "/api/calculation-methods/{inspectionObjectCode}/{inspectionParameterCode}",
    responses={
        200: {"model": CalculationMethod, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["calculation-methods"],
    response_model_by_alias=True,
)
async def calculation_methods_update_calculation_method(
    inspectionObjectCode: StrictStr = Path(..., description=""),
    inspectionParameterCode: StrictStr = Path(..., description=""),
    update_calculation_method_request: UpdateCalculationMethodRequest = Body(None, description=""),
) -> CalculationMethod:
    if not BaseCalculationMethodsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCalculationMethodsApi.subclasses[0]().calculation_methods_update_calculation_method(inspectionObjectCode, inspectionParameterCode, update_calculation_method_request)


@router.delete(
    "/api/calculation-methods/{inspectionObjectCode}/{inspectionParameterCode}",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["calculation-methods"],
    response_model_by_alias=True,
)
async def calculation_methods_delete_calculation_method(
    inspectionObjectCode: StrictStr = Path(..., description=""),
    inspectionParameterCode: StrictStr = Path(..., description=""),
) -> None:
    if not BaseCalculationMethodsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseCalculationMethodsApi.subclasses[0]().calculation_methods_delete_calculation_method(inspectionObjectCode, inspectionParameterCode)
