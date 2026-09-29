# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from lab_management_system_fastapi.apis.inspection_catalog_api_base import BaseInspectionCatalogApi
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
from lab_management_system_fastapi.models.catalog_list_brands200_response import CatalogListBrands200Response
from lab_management_system_fastapi.models.catalog_list_grades200_response import CatalogListGrades200Response
from lab_management_system_fastapi.models.catalog_list_models200_response import CatalogListModels200Response
from lab_management_system_fastapi.models.catalog_list_specs200_response import CatalogListSpecs200Response
from lab_management_system_fastapi.models.create_catalog_entry_request import CreateCatalogEntryRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.inspection_brand import InspectionBrand
from lab_management_system_fastapi.models.inspection_grade import InspectionGrade
from lab_management_system_fastapi.models.inspection_model import InspectionModel
from lab_management_system_fastapi.models.inspection_spec import InspectionSpec
from lab_management_system_fastapi.models.update_catalog_entry_request import UpdateCatalogEntryRequest


router = APIRouter()

ns_pkg = lab_management_system_fastapi.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/catalog/brands",
    responses={
        200: {"model": CatalogListBrands200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-catalog"],
    response_model_by_alias=True,
)
async def catalog_list_brands(
    page: Optional[StrictInt] = Query(None, description="", alias="page"),
    page_size: Optional[StrictInt] = Query(None, description="", alias="pageSize"),
    inspection_object_code: Optional[StrictStr] = Query(None, description="", alias="inspectionObjectCode"),
    keyword: Optional[StrictStr] = Query(None, description="", alias="keyword"),
) -> CatalogListBrands200Response:
    if not BaseInspectionCatalogApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionCatalogApi.subclasses[0]().catalog_list_brands(page, page_size, inspection_object_code, keyword)


@router.post(
    "/api/catalog/brands",
    responses={
        200: {"model": InspectionBrand, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-catalog"],
    response_model_by_alias=True,
)
async def catalog_create_brand(
    create_catalog_entry_request: CreateCatalogEntryRequest = Body(None, description=""),
) -> InspectionBrand:
    if not BaseInspectionCatalogApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionCatalogApi.subclasses[0]().catalog_create_brand(create_catalog_entry_request)


@router.put(
    "/api/catalog/brands/{code}",
    responses={
        200: {"model": InspectionBrand, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-catalog"],
    response_model_by_alias=True,
)
async def catalog_update_brand(
    code: StrictStr = Path(..., description=""),
    update_catalog_entry_request: UpdateCatalogEntryRequest = Body(None, description=""),
) -> InspectionBrand:
    if not BaseInspectionCatalogApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionCatalogApi.subclasses[0]().catalog_update_brand(code, update_catalog_entry_request)


@router.delete(
    "/api/catalog/brands/{code}",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-catalog"],
    response_model_by_alias=True,
)
async def catalog_delete_brand(
    code: StrictStr = Path(..., description=""),
) -> None:
    if not BaseInspectionCatalogApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionCatalogApi.subclasses[0]().catalog_delete_brand(code)


@router.get(
    "/api/catalog/grades",
    responses={
        200: {"model": CatalogListGrades200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-catalog"],
    response_model_by_alias=True,
)
async def catalog_list_grades(
    page: Optional[StrictInt] = Query(None, description="", alias="page"),
    page_size: Optional[StrictInt] = Query(None, description="", alias="pageSize"),
    inspection_object_code: Optional[StrictStr] = Query(None, description="", alias="inspectionObjectCode"),
    keyword: Optional[StrictStr] = Query(None, description="", alias="keyword"),
) -> CatalogListGrades200Response:
    if not BaseInspectionCatalogApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionCatalogApi.subclasses[0]().catalog_list_grades(page, page_size, inspection_object_code, keyword)


@router.post(
    "/api/catalog/grades",
    responses={
        200: {"model": InspectionGrade, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-catalog"],
    response_model_by_alias=True,
)
async def catalog_create_grade(
    create_catalog_entry_request: CreateCatalogEntryRequest = Body(None, description=""),
) -> InspectionGrade:
    if not BaseInspectionCatalogApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionCatalogApi.subclasses[0]().catalog_create_grade(create_catalog_entry_request)


@router.put(
    "/api/catalog/grades/{code}",
    responses={
        200: {"model": InspectionGrade, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-catalog"],
    response_model_by_alias=True,
)
async def catalog_update_grade(
    code: StrictStr = Path(..., description=""),
    update_catalog_entry_request: UpdateCatalogEntryRequest = Body(None, description=""),
) -> InspectionGrade:
    if not BaseInspectionCatalogApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionCatalogApi.subclasses[0]().catalog_update_grade(code, update_catalog_entry_request)


@router.delete(
    "/api/catalog/grades/{code}",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-catalog"],
    response_model_by_alias=True,
)
async def catalog_delete_grade(
    code: StrictStr = Path(..., description=""),
) -> None:
    if not BaseInspectionCatalogApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionCatalogApi.subclasses[0]().catalog_delete_grade(code)


@router.get(
    "/api/catalog/models",
    responses={
        200: {"model": CatalogListModels200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-catalog"],
    response_model_by_alias=True,
)
async def catalog_list_models(
    page: Optional[StrictInt] = Query(None, description="", alias="page"),
    page_size: Optional[StrictInt] = Query(None, description="", alias="pageSize"),
    inspection_object_code: Optional[StrictStr] = Query(None, description="", alias="inspectionObjectCode"),
    keyword: Optional[StrictStr] = Query(None, description="", alias="keyword"),
) -> CatalogListModels200Response:
    if not BaseInspectionCatalogApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionCatalogApi.subclasses[0]().catalog_list_models(page, page_size, inspection_object_code, keyword)


@router.post(
    "/api/catalog/models",
    responses={
        200: {"model": InspectionModel, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-catalog"],
    response_model_by_alias=True,
)
async def catalog_create_model(
    create_catalog_entry_request: CreateCatalogEntryRequest = Body(None, description=""),
) -> InspectionModel:
    if not BaseInspectionCatalogApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionCatalogApi.subclasses[0]().catalog_create_model(create_catalog_entry_request)


@router.put(
    "/api/catalog/models/{code}",
    responses={
        200: {"model": InspectionModel, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-catalog"],
    response_model_by_alias=True,
)
async def catalog_update_model(
    code: StrictStr = Path(..., description=""),
    update_catalog_entry_request: UpdateCatalogEntryRequest = Body(None, description=""),
) -> InspectionModel:
    if not BaseInspectionCatalogApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionCatalogApi.subclasses[0]().catalog_update_model(code, update_catalog_entry_request)


@router.delete(
    "/api/catalog/models/{code}",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-catalog"],
    response_model_by_alias=True,
)
async def catalog_delete_model(
    code: StrictStr = Path(..., description=""),
) -> None:
    if not BaseInspectionCatalogApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionCatalogApi.subclasses[0]().catalog_delete_model(code)


@router.get(
    "/api/catalog/specs",
    responses={
        200: {"model": CatalogListSpecs200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-catalog"],
    response_model_by_alias=True,
)
async def catalog_list_specs(
    page: Optional[StrictInt] = Query(None, description="", alias="page"),
    page_size: Optional[StrictInt] = Query(None, description="", alias="pageSize"),
    inspection_object_code: Optional[StrictStr] = Query(None, description="", alias="inspectionObjectCode"),
    keyword: Optional[StrictStr] = Query(None, description="", alias="keyword"),
) -> CatalogListSpecs200Response:
    if not BaseInspectionCatalogApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionCatalogApi.subclasses[0]().catalog_list_specs(page, page_size, inspection_object_code, keyword)


@router.post(
    "/api/catalog/specs",
    responses={
        200: {"model": InspectionSpec, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-catalog"],
    response_model_by_alias=True,
)
async def catalog_create_spec(
    create_catalog_entry_request: CreateCatalogEntryRequest = Body(None, description=""),
) -> InspectionSpec:
    if not BaseInspectionCatalogApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionCatalogApi.subclasses[0]().catalog_create_spec(create_catalog_entry_request)


@router.put(
    "/api/catalog/specs/{code}",
    responses={
        200: {"model": InspectionSpec, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-catalog"],
    response_model_by_alias=True,
)
async def catalog_update_spec(
    code: StrictStr = Path(..., description=""),
    update_catalog_entry_request: UpdateCatalogEntryRequest = Body(None, description=""),
) -> InspectionSpec:
    if not BaseInspectionCatalogApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionCatalogApi.subclasses[0]().catalog_update_spec(code, update_catalog_entry_request)


@router.delete(
    "/api/catalog/specs/{code}",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["inspection-catalog"],
    response_model_by_alias=True,
)
async def catalog_delete_spec(
    code: StrictStr = Path(..., description=""),
) -> None:
    if not BaseInspectionCatalogApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseInspectionCatalogApi.subclasses[0]().catalog_delete_spec(code)
