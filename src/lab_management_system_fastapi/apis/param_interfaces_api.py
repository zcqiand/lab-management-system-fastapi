# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from lab_management_system_fastapi.apis.param_interfaces_api_base import BaseParamInterfacesApi
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
from lab_management_system_fastapi.models.create_param_interface_request import CreateParamInterfaceRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.param_interface import ParamInterface
from lab_management_system_fastapi.models.param_interface_link import ParamInterfaceLink
from lab_management_system_fastapi.models.param_interfaces_list_param_interface_links200_response import ParamInterfacesListParamInterfaceLinks200Response
from lab_management_system_fastapi.models.param_interfaces_list_param_interfaces200_response import ParamInterfacesListParamInterfaces200Response
from lab_management_system_fastapi.models.param_interfaces_unlink_param_interface_request import ParamInterfacesUnlinkParamInterfaceRequest
from lab_management_system_fastapi.models.update_param_interface_request import UpdateParamInterfaceRequest


router = APIRouter()

ns_pkg = lab_management_system_fastapi.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/param-interfaces",
    responses={
        200: {"model": ParamInterfacesListParamInterfaces200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["param-interfaces"],
    response_model_by_alias=True,
)
async def param_interfaces_list_param_interfaces(
    page: Optional[StrictInt] = Query(None, description="", alias="page"),
    page_size: Optional[StrictInt] = Query(None, description="", alias="pageSize"),
    keyword: Optional[StrictStr] = Query(None, description="", alias="keyword"),
) -> ParamInterfacesListParamInterfaces200Response:
    if not BaseParamInterfacesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseParamInterfacesApi.subclasses[0]().param_interfaces_list_param_interfaces(page, page_size, keyword)


@router.post(
    "/api/param-interfaces",
    responses={
        200: {"model": ParamInterface, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["param-interfaces"],
    response_model_by_alias=True,
)
async def param_interfaces_create_param_interface(
    create_param_interface_request: CreateParamInterfaceRequest = Body(None, description=""),
) -> ParamInterface:
    if not BaseParamInterfacesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseParamInterfacesApi.subclasses[0]().param_interfaces_create_param_interface(create_param_interface_request)


@router.get(
    "/api/param-interfaces/links",
    responses={
        200: {"model": ParamInterfacesListParamInterfaceLinks200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["param-interfaces"],
    response_model_by_alias=True,
)
async def param_interfaces_list_param_interface_links(
    inspection_parameter_code: Optional[StrictStr] = Query(None, description="", alias="inspectionParameterCode"),
    param_interface_code: Optional[StrictStr] = Query(None, description="", alias="paramInterfaceCode"),
) -> ParamInterfacesListParamInterfaceLinks200Response:
    if not BaseParamInterfacesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseParamInterfacesApi.subclasses[0]().param_interfaces_list_param_interface_links(inspection_parameter_code, param_interface_code)


@router.post(
    "/api/param-interfaces/links",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["param-interfaces"],
    response_model_by_alias=True,
)
async def param_interfaces_link_param_interface(
    param_interface_link: ParamInterfaceLink = Body(None, description=""),
) -> None:
    if not BaseParamInterfacesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseParamInterfacesApi.subclasses[0]().param_interfaces_link_param_interface(param_interface_link)


@router.delete(
    "/api/param-interfaces/links",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["param-interfaces"],
    response_model_by_alias=True,
)
async def param_interfaces_unlink_param_interface(
    param_interfaces_unlink_param_interface_request: ParamInterfacesUnlinkParamInterfaceRequest = Body(None, description=""),
) -> None:
    if not BaseParamInterfacesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseParamInterfacesApi.subclasses[0]().param_interfaces_unlink_param_interface(param_interfaces_unlink_param_interface_request)


@router.get(
    "/api/param-interfaces/{code}",
    responses={
        200: {"model": ParamInterface, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["param-interfaces"],
    response_model_by_alias=True,
)
async def param_interfaces_get_param_interface(
    code: StrictStr = Path(..., description=""),
) -> ParamInterface:
    if not BaseParamInterfacesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseParamInterfacesApi.subclasses[0]().param_interfaces_get_param_interface(code)


@router.put(
    "/api/param-interfaces/{code}",
    responses={
        200: {"model": ParamInterface, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["param-interfaces"],
    response_model_by_alias=True,
)
async def param_interfaces_update_param_interface(
    code: StrictStr = Path(..., description=""),
    update_param_interface_request: UpdateParamInterfaceRequest = Body(None, description=""),
) -> ParamInterface:
    if not BaseParamInterfacesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseParamInterfacesApi.subclasses[0]().param_interfaces_update_param_interface(code, update_param_interface_request)


@router.delete(
    "/api/param-interfaces/{code}",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["param-interfaces"],
    response_model_by_alias=True,
)
async def param_interfaces_delete_param_interface(
    code: StrictStr = Path(..., description=""),
) -> None:
    if not BaseParamInterfacesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseParamInterfacesApi.subclasses[0]().param_interfaces_delete_param_interface(code)
