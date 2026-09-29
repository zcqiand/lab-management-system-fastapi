# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from lab_management_system_fastapi.apis.test_records_api_base import BaseTestRecordsApi
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
from lab_management_system_fastapi.models.create_test_record_request import CreateTestRecordRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.test_record import TestRecord
from lab_management_system_fastapi.models.test_records_list_test_records200_response import TestRecordsListTestRecords200Response
from lab_management_system_fastapi.models.test_records_set_verdict_request import TestRecordsSetVerdictRequest
from lab_management_system_fastapi.models.update_test_record_request import UpdateTestRecordRequest


router = APIRouter()

ns_pkg = lab_management_system_fastapi.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/test-records",
    responses={
        200: {"model": TestRecordsListTestRecords200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["test-records"],
    response_model_by_alias=True,
)
async def test_records_list_test_records(
    page: Optional[StrictInt] = Query(None, description="", alias="page"),
    page_size: Optional[StrictInt] = Query(None, description="", alias="pageSize"),
    sample_id: Optional[StrictStr] = Query(None, description="", alias="sampleId"),
    parameter_code: Optional[StrictStr] = Query(None, description="", alias="parameterCode"),
) -> TestRecordsListTestRecords200Response:
    if not BaseTestRecordsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseTestRecordsApi.subclasses[0]().test_records_list_test_records(page, page_size, sample_id, parameter_code)


@router.post(
    "/api/test-records",
    responses={
        200: {"model": TestRecord, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["test-records"],
    response_model_by_alias=True,
)
async def test_records_create_test_record(
    create_test_record_request: CreateTestRecordRequest = Body(None, description=""),
) -> TestRecord:
    if not BaseTestRecordsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseTestRecordsApi.subclasses[0]().test_records_create_test_record(create_test_record_request)


@router.get(
    "/api/test-records/{id}",
    responses={
        200: {"model": TestRecord, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["test-records"],
    response_model_by_alias=True,
)
async def test_records_get_test_record(
    id: StrictStr = Path(..., description=""),
) -> TestRecord:
    if not BaseTestRecordsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseTestRecordsApi.subclasses[0]().test_records_get_test_record(id)


@router.put(
    "/api/test-records/{id}",
    responses={
        200: {"model": TestRecord, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["test-records"],
    response_model_by_alias=True,
)
async def test_records_update_test_record(
    id: StrictStr = Path(..., description=""),
    update_test_record_request: UpdateTestRecordRequest = Body(None, description=""),
) -> TestRecord:
    if not BaseTestRecordsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseTestRecordsApi.subclasses[0]().test_records_update_test_record(id, update_test_record_request)


@router.delete(
    "/api/test-records/{id}",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["test-records"],
    response_model_by_alias=True,
)
async def test_records_delete_test_record(
    id: StrictStr = Path(..., description=""),
) -> None:
    if not BaseTestRecordsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseTestRecordsApi.subclasses[0]().test_records_delete_test_record(id)


@router.patch(
    "/api/test-records/{id}/verdict",
    responses={
        200: {"model": TestRecord, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["test-records"],
    response_model_by_alias=True,
)
async def test_records_set_verdict(
    id: StrictStr = Path(..., description=""),
    test_records_set_verdict_request: TestRecordsSetVerdictRequest = Body(None, description=""),
) -> TestRecord:
    if not BaseTestRecordsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseTestRecordsApi.subclasses[0]().test_records_set_verdict(id, test_records_set_verdict_request)
