# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from lab_management_system_fastapi.apis.samples_api_base import BaseSamplesApi
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
from lab_management_system_fastapi.models.create_sample_request import CreateSampleRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.sample import Sample
from lab_management_system_fastapi.models.samples_list_samples200_response import SamplesListSamples200Response
from lab_management_system_fastapi.models.update_sample_ext_request import UpdateSampleExtRequest
from lab_management_system_fastapi.models.update_sample_request import UpdateSampleRequest


router = APIRouter()

ns_pkg = lab_management_system_fastapi.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/samples",
    responses={
        200: {"model": SamplesListSamples200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["samples"],
    response_model_by_alias=True,
)
async def samples_list_samples(
    page: Optional[StrictInt] = Query(None, description="", alias="page"),
    page_size: Optional[StrictInt] = Query(None, description="", alias="pageSize"),
    receipt_id: Optional[StrictStr] = Query(None, description="", alias="receiptId"),
    keyword: Optional[StrictStr] = Query(None, description="", alias="keyword"),
) -> SamplesListSamples200Response:
    if not BaseSamplesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseSamplesApi.subclasses[0]().samples_list_samples(page, page_size, receipt_id, keyword)


@router.post(
    "/api/samples",
    responses={
        200: {"model": Sample, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["samples"],
    response_model_by_alias=True,
)
async def samples_create_sample(
    create_sample_request: CreateSampleRequest = Body(None, description=""),
) -> Sample:
    if not BaseSamplesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseSamplesApi.subclasses[0]().samples_create_sample(create_sample_request)


@router.get(
    "/api/samples/{id}",
    responses={
        200: {"model": Sample, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["samples"],
    response_model_by_alias=True,
)
async def samples_get_sample(
    id: StrictStr = Path(..., description=""),
) -> Sample:
    if not BaseSamplesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseSamplesApi.subclasses[0]().samples_get_sample(id)


@router.put(
    "/api/samples/{id}",
    responses={
        200: {"model": Sample, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["samples"],
    response_model_by_alias=True,
)
async def samples_update_sample(
    id: StrictStr = Path(..., description=""),
    update_sample_request: UpdateSampleRequest = Body(None, description=""),
) -> Sample:
    if not BaseSamplesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseSamplesApi.subclasses[0]().samples_update_sample(id, update_sample_request)


@router.delete(
    "/api/samples/{id}",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["samples"],
    response_model_by_alias=True,
)
async def samples_delete_sample(
    id: StrictStr = Path(..., description=""),
) -> None:
    if not BaseSamplesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseSamplesApi.subclasses[0]().samples_delete_sample(id)


@router.put(
    "/api/samples/{id}/ext",
    responses={
        200: {"model": Sample, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["samples"],
    response_model_by_alias=True,
)
async def samples_update_sample_ext(
    id: StrictStr = Path(..., description=""),
    update_sample_ext_request: UpdateSampleExtRequest = Body(None, description=""),
) -> Sample:
    if not BaseSamplesApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseSamplesApi.subclasses[0]().samples_update_sample_ext(id, update_sample_ext_request)
