# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from lab_management_system_fastapi.apis.inspection_dictionary_api_base import BaseInspectionDictionaryApi
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
from lab_management_system_fastapi.models.create_inspection_object_request import CreateInspectionObjectRequest
from lab_management_system_fastapi.models.create_inspection_parameter_request import CreateInspectionParameterRequest
from lab_management_system_fastapi.models.create_inspection_specialty_request import CreateInspectionSpecialtyRequest
from lab_management_system_fastapi.models.create_inspection_standard_request import CreateInspectionStandardRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.inspection_dictionary_list_object_parameter_links200_response import InspectionDictionaryListObjectParameterLinks200Response
from lab_management_system_fastapi.models.inspection_dictionary_list_object_standard_links200_response import InspectionDictionaryListObjectStandardLinks200Response
from lab_management_system_fastapi.models.inspection_dictionary_list_objects200_response import InspectionDictionaryListObjects200Response
from lab_management_system_fastapi.models.inspection_dictionary_list_parameters200_response import InspectionDictionaryListParameters200Response
from lab_management_system_fastapi.models.inspection_dictionary_list_specialties200_response import InspectionDictionaryListSpecialties200Response
from lab_management_system_fastapi.models.inspection_dictionary_list_specialty_object_links200_response import InspectionDictionaryListSpecialtyObjectLinks200Response
from lab_management_system_fastapi.models.inspection_dictionary_list_standard_parameter_links200_response import InspectionDictionaryListStandardParameterLinks200Response
from lab_management_system_fastapi.models.inspection_dictionary_list_standards200_response import InspectionDictionaryListStandards200Response
from lab_management_system_fastapi.models.inspection_dictionary_unlink_object_parameter_request import InspectionDictionaryUnlinkObjectParameterRequest
from lab_management_system_fastapi.models.inspection_dictionary_unlink_object_standard_request import InspectionDictionaryUnlinkObjectStandardRequest
from lab_management_system_fastapi.models.inspection_object import InspectionObject
from lab_management_system_fastapi.models.inspection_parameter import InspectionParameter
from lab_management_system_fastapi.models.inspection_parameter_source_type import InspectionParameterSourceType
from lab_management_system_fastapi.models.inspection_specialty import InspectionSpecialty
from lab_management_system_fastapi.models.inspection_standard import InspectionStandard
from lab_management_system_fastapi.models.inspection_standard_role import InspectionStandardRole
from lab_management_system_fastapi.models.inspection_standard_status import InspectionStandardStatus
from lab_management_system_fastapi.models.object_parameter_link import ObjectParameterLink
from lab_management_system_fastapi.models.object_standard_link import ObjectStandardLink
from lab_management_system_fastapi.models.specialty_object_link import SpecialtyObjectLink
from lab_management_system_fastapi.models.standard_parameter_link import StandardParameterLink
from lab_management_system_fastapi.models.update_inspection_object_request import UpdateInspectionObjectRequest
from lab_management_system_fastapi.models.update_inspection_parameter_request import UpdateInspectionParameterRequest
from lab_management_system_fastapi.models.update_inspection_specialty_request import UpdateInspectionSpecialtyRequest
from lab_management_system_fastapi.models.update_inspection_standard_request import UpdateInspectionStandardRequest


router = APIRouter()

ns_pkg = lab_management_system_fastapi.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/inspection/links/object-parameter",
    responses={
        200: {"model": InspectionDictionaryListObjectParameterLinks200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_list_object_parameter_links(
    inspection_object_code: Optional[StrictStr] = Query(None, description="", alias="inspectionObjectCode"),
    inspection_parameter_code: Optional[StrictStr] = Query(None, description="", alias="inspectionParameterCode"),
) -> InspectionDictionaryListObjectParameterLinks200Response:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_list_object_parameter_links(inspection_object_code, inspection_parameter_code)


@router.post(
    "/api/inspection/links/object-parameter",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_link_object_parameter(
    object_parameter_link: ObjectParameterLink = Body(None, description=""),
) -> None:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_link_object_parameter(object_parameter_link)


@router.delete(
    "/api/inspection/links/object-parameter",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_unlink_object_parameter(
    inspection_dictionary_unlink_object_parameter_request: InspectionDictionaryUnlinkObjectParameterRequest = Body(None, description=""),
) -> None:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_unlink_object_parameter(inspection_dictionary_unlink_object_parameter_request)


@router.get(
    "/api/inspection/links/object-standard",
    responses={
        200: {"model": InspectionDictionaryListObjectStandardLinks200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_list_object_standard_links(
    inspection_object_code: Optional[StrictStr] = Query(None, description="", alias="inspectionObjectCode"),
    role: Optional[InspectionStandardRole] = Query(None, description="", alias="role"),
) -> InspectionDictionaryListObjectStandardLinks200Response:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_list_object_standard_links(inspection_object_code, role)


@router.post(
    "/api/inspection/links/object-standard",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_link_object_standard(
    object_standard_link: ObjectStandardLink = Body(None, description=""),
) -> None:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_link_object_standard(object_standard_link)


@router.delete(
    "/api/inspection/links/object-standard",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_unlink_object_standard(
    inspection_dictionary_unlink_object_standard_request: InspectionDictionaryUnlinkObjectStandardRequest = Body(None, description=""),
) -> None:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_unlink_object_standard(inspection_dictionary_unlink_object_standard_request)


@router.get(
    "/api/inspection/links/specialty-object",
    responses={
        200: {"model": InspectionDictionaryListSpecialtyObjectLinks200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_list_specialty_object_links(
    inspection_specialty_code: Optional[StrictStr] = Query(None, description="", alias="inspectionSpecialtyCode"),
) -> InspectionDictionaryListSpecialtyObjectLinks200Response:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_list_specialty_object_links(inspection_specialty_code)


@router.post(
    "/api/inspection/links/specialty-object",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_link_specialty_object(
    specialty_object_link: SpecialtyObjectLink = Body(None, description=""),
) -> None:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_link_specialty_object(specialty_object_link)


@router.delete(
    "/api/inspection/links/specialty-object",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_unlink_specialty_object(
    specialty_object_link: SpecialtyObjectLink = Body(None, description=""),
) -> None:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_unlink_specialty_object(specialty_object_link)


@router.get(
    "/api/inspection/links/standard-parameter",
    responses={
        200: {"model": InspectionDictionaryListStandardParameterLinks200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_list_standard_parameter_links(
    inspection_standard_code: Optional[StrictStr] = Query(None, description="", alias="inspectionStandardCode"),
    inspection_parameter_code: Optional[StrictStr] = Query(None, description="", alias="inspectionParameterCode"),
) -> InspectionDictionaryListStandardParameterLinks200Response:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_list_standard_parameter_links(inspection_standard_code, inspection_parameter_code)


@router.post(
    "/api/inspection/links/standard-parameter",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_link_standard_parameter(
    standard_parameter_link: StandardParameterLink = Body(None, description=""),
) -> None:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_link_standard_parameter(standard_parameter_link)


@router.delete(
    "/api/inspection/links/standard-parameter",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_unlink_standard_parameter(
    standard_parameter_link: StandardParameterLink = Body(None, description=""),
) -> None:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_unlink_standard_parameter(standard_parameter_link)


@router.get(
    "/api/inspection/objects",
    responses={
        200: {"model": InspectionDictionaryListObjects200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_list_objects(
    page: Optional[StrictInt] = Query(None, description="", alias="page"),
    page_size: Optional[StrictInt] = Query(None, description="", alias="pageSize"),
    inspection_specialty_code: Optional[StrictStr] = Query(None, description="", alias="inspectionSpecialtyCode"),
    keyword: Optional[StrictStr] = Query(None, description="", alias="keyword"),
) -> InspectionDictionaryListObjects200Response:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_list_objects(page, page_size, inspection_specialty_code, keyword)


@router.post(
    "/api/inspection/objects",
    responses={
        200: {"model": InspectionObject, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_create_object(
    create_inspection_object_request: CreateInspectionObjectRequest = Body(None, description=""),
) -> InspectionObject:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_create_object(create_inspection_object_request)


@router.put(
    "/api/inspection/objects/{code}",
    responses={
        200: {"model": InspectionObject, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_update_object(
    code: StrictStr = Path(..., description=""),
    update_inspection_object_request: UpdateInspectionObjectRequest = Body(None, description=""),
) -> InspectionObject:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_update_object(code, update_inspection_object_request)


@router.delete(
    "/api/inspection/objects/{code}",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_delete_object(
    code: StrictStr = Path(..., description=""),
) -> None:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_delete_object(code)


@router.get(
    "/api/inspection/parameters",
    responses={
        200: {"model": InspectionDictionaryListParameters200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_list_parameters(
    page: Optional[StrictInt] = Query(None, description="", alias="page"),
    page_size: Optional[StrictInt] = Query(None, description="", alias="pageSize"),
    keyword: Optional[StrictStr] = Query(None, description="", alias="keyword"),
    source_type: Optional[InspectionParameterSourceType] = Query(None, description="", alias="sourceType"),
) -> InspectionDictionaryListParameters200Response:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_list_parameters(page, page_size, keyword, source_type)


@router.post(
    "/api/inspection/parameters",
    responses={
        200: {"model": InspectionParameter, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_create_parameter(
    create_inspection_parameter_request: CreateInspectionParameterRequest = Body(None, description=""),
) -> InspectionParameter:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_create_parameter(create_inspection_parameter_request)


@router.put(
    "/api/inspection/parameters/{code}",
    responses={
        200: {"model": InspectionParameter, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_update_parameter(
    code: StrictStr = Path(..., description=""),
    update_inspection_parameter_request: UpdateInspectionParameterRequest = Body(None, description=""),
) -> InspectionParameter:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_update_parameter(code, update_inspection_parameter_request)


@router.delete(
    "/api/inspection/parameters/{code}",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_delete_parameter(
    code: StrictStr = Path(..., description=""),
) -> None:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_delete_parameter(code)


@router.get(
    "/api/inspection/specialties",
    responses={
        200: {"model": InspectionDictionaryListSpecialties200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_list_specialties(
    page: Optional[StrictInt] = Query(None, description="", alias="page"),
    page_size: Optional[StrictInt] = Query(None, description="", alias="pageSize"),
    keyword: Optional[StrictStr] = Query(None, description="", alias="keyword"),
) -> InspectionDictionaryListSpecialties200Response:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_list_specialties(page, page_size, keyword)


@router.post(
    "/api/inspection/specialties",
    responses={
        200: {"model": InspectionSpecialty, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_create_specialty(
    create_inspection_specialty_request: CreateInspectionSpecialtyRequest = Body(None, description=""),
) -> InspectionSpecialty:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_create_specialty(create_inspection_specialty_request)


@router.put(
    "/api/inspection/specialties/{code}",
    responses={
        200: {"model": InspectionSpecialty, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_update_specialty(
    code: StrictStr = Path(..., description=""),
    update_inspection_specialty_request: UpdateInspectionSpecialtyRequest = Body(None, description=""),
) -> InspectionSpecialty:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_update_specialty(code, update_inspection_specialty_request)


@router.delete(
    "/api/inspection/specialties/{code}",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_delete_specialty(
    code: StrictStr = Path(..., description=""),
) -> None:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_delete_specialty(code)


@router.get(
    "/api/inspection/standards",
    responses={
        200: {"model": InspectionDictionaryListStandards200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_list_standards(
    page: Optional[StrictInt] = Query(None, description="", alias="page"),
    page_size: Optional[StrictInt] = Query(None, description="", alias="pageSize"),
    keyword: Optional[StrictStr] = Query(None, description="", alias="keyword"),
    status: Optional[InspectionStandardStatus] = Query(None, description="", alias="status"),
) -> InspectionDictionaryListStandards200Response:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_list_standards(page, page_size, keyword, status)


@router.post(
    "/api/inspection/standards",
    responses={
        200: {"model": InspectionStandard, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_create_standard(
    create_inspection_standard_request: CreateInspectionStandardRequest = Body(None, description=""),
) -> InspectionStandard:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_create_standard(create_inspection_standard_request)


@router.put(
    "/api/inspection/standards/{code}",
    responses={
        200: {"model": InspectionStandard, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_update_standard(
    code: StrictStr = Path(..., description=""),
    update_inspection_standard_request: UpdateInspectionStandardRequest = Body(None, description=""),
) -> InspectionStandard:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_update_standard(code, update_inspection_standard_request)


@router.delete(
    "/api/inspection/standards/{code}",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-dictionary"],
    response_model_by_alias=True,
)
async def inspection_dictionary_delete_standard(
    code: StrictStr = Path(..., description=""),
) -> None:
    if not BaseInspectionDictionaryApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionDictionaryApi.subclasses[0]().inspection_dictionary_delete_standard(code)
