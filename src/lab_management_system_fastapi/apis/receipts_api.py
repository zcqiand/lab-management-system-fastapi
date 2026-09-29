# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from lab_management_system_fastapi.apis.receipts_api_base import BaseReceiptsApi
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
from typing import Any, List, Optional
from lab_management_system_fastapi.models.assign_task_request import AssignTaskRequest
from lab_management_system_fastapi.models.create_sample_receipt_request import CreateSampleReceiptRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.flow_action_request import FlowActionRequest
from lab_management_system_fastapi.models.flow_action_result import FlowActionResult
from lab_management_system_fastapi.models.flow_history_entry import FlowHistoryEntry
from lab_management_system_fastapi.models.flow_status import FlowStatus
from lab_management_system_fastapi.models.receipts_list_receipts200_response import ReceiptsListReceipts200Response
from lab_management_system_fastapi.models.sample_receipt import SampleReceipt
from lab_management_system_fastapi.models.update_sample_receipt_request import UpdateSampleReceiptRequest


router = APIRouter()

ns_pkg = lab_management_system_fastapi.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/receipts",
    responses={
        200: {"model": ReceiptsListReceipts200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["receipts"],
    response_model_by_alias=True,
)
async def receipts_list_receipts(
    page: Optional[StrictInt] = Query(None, description="", alias="page"),
    page_size: Optional[StrictInt] = Query(None, description="", alias="pageSize"),
    keyword: Optional[StrictStr] = Query(None, description="", alias="keyword"),
    contract_id: Optional[StrictStr] = Query(None, description="", alias="contractId"),
    flow_status: Optional[FlowStatus] = Query(None, description="", alias="flowStatus"),
    filter: Optional[StrictStr] = Query(None, description="", alias="filter"),
) -> ReceiptsListReceipts200Response:
    if not BaseReceiptsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReceiptsApi.subclasses[0]().receipts_list_receipts(page, page_size, keyword, contract_id, flow_status, filter)


@router.post(
    "/api/receipts",
    responses={
        200: {"model": SampleReceipt, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["receipts"],
    response_model_by_alias=True,
)
async def receipts_create_receipt(
    create_sample_receipt_request: CreateSampleReceiptRequest = Body(None, description=""),
) -> SampleReceipt:
    if not BaseReceiptsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReceiptsApi.subclasses[0]().receipts_create_receipt(create_sample_receipt_request)


@router.post(
    "/api/receipts/approve/act",
    responses={
        200: {"model": List[FlowActionResult], "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["receipts"],
    response_model_by_alias=True,
)
async def receipts_act_flow_approve(
    flow_action_request: FlowActionRequest = Body(None, description=""),
) -> List[FlowActionResult]:
    if not BaseReceiptsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReceiptsApi.subclasses[0]().receipts_act_flow_approve(flow_action_request)


@router.post(
    "/api/receipts/archived/act",
    responses={
        200: {"model": List[FlowActionResult], "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["receipts"],
    response_model_by_alias=True,
)
async def receipts_act_flow_archived(
    flow_action_request: FlowActionRequest = Body(None, description=""),
) -> List[FlowActionResult]:
    if not BaseReceiptsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReceiptsApi.subclasses[0]().receipts_act_flow_archived(flow_action_request)


@router.post(
    "/api/receipts/assigning/act",
    responses={
        200: {"model": List[FlowActionResult], "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["receipts"],
    response_model_by_alias=True,
)
async def receipts_act_flow_assigning(
    flow_action_request: FlowActionRequest = Body(None, description=""),
) -> List[FlowActionResult]:
    if not BaseReceiptsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReceiptsApi.subclasses[0]().receipts_act_flow_assigning(flow_action_request)


@router.post(
    "/api/receipts/data-entry/act",
    responses={
        200: {"model": List[FlowActionResult], "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["receipts"],
    response_model_by_alias=True,
)
async def receipts_act_flow_data_entry(
    flow_action_request: FlowActionRequest = Body(None, description=""),
) -> List[FlowActionResult]:
    if not BaseReceiptsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReceiptsApi.subclasses[0]().receipts_act_flow_data_entry(flow_action_request)


@router.post(
    "/api/receipts/issuance/act",
    responses={
        200: {"model": List[FlowActionResult], "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["receipts"],
    response_model_by_alias=True,
)
async def receipts_act_flow_issuance(
    flow_action_request: FlowActionRequest = Body(None, description=""),
) -> List[FlowActionResult]:
    if not BaseReceiptsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReceiptsApi.subclasses[0]().receipts_act_flow_issuance(flow_action_request)


@router.post(
    "/api/receipts/receiving/act",
    responses={
        200: {"model": List[FlowActionResult], "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["receipts"],
    response_model_by_alias=True,
)
async def receipts_act_flow_receiving(
    flow_action_request: FlowActionRequest = Body(None, description=""),
) -> List[FlowActionResult]:
    if not BaseReceiptsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReceiptsApi.subclasses[0]().receipts_act_flow_receiving(flow_action_request)


@router.post(
    "/api/receipts/review/act",
    responses={
        200: {"model": List[FlowActionResult], "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["receipts"],
    response_model_by_alias=True,
)
async def receipts_act_flow_review(
    flow_action_request: FlowActionRequest = Body(None, description=""),
) -> List[FlowActionResult]:
    if not BaseReceiptsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReceiptsApi.subclasses[0]().receipts_act_flow_review(flow_action_request)


@router.get(
    "/api/receipts/{id}",
    responses={
        200: {"model": SampleReceipt, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["receipts"],
    response_model_by_alias=True,
)
async def receipts_get_receipt(
    id: StrictStr = Path(..., description=""),
) -> SampleReceipt:
    if not BaseReceiptsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReceiptsApi.subclasses[0]().receipts_get_receipt(id)


@router.put(
    "/api/receipts/{id}",
    responses={
        200: {"model": SampleReceipt, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["receipts"],
    response_model_by_alias=True,
)
async def receipts_update_receipt(
    id: StrictStr = Path(..., description=""),
    update_sample_receipt_request: UpdateSampleReceiptRequest = Body(None, description=""),
) -> SampleReceipt:
    if not BaseReceiptsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReceiptsApi.subclasses[0]().receipts_update_receipt(id, update_sample_receipt_request)


@router.delete(
    "/api/receipts/{id}",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["receipts"],
    response_model_by_alias=True,
)
async def receipts_delete_receipt(
    id: StrictStr = Path(..., description=""),
) -> None:
    if not BaseReceiptsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReceiptsApi.subclasses[0]().receipts_delete_receipt(id)


@router.get(
    "/api/receipts/{id}/history",
    responses={
        200: {"model": List[FlowHistoryEntry], "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["receipts"],
    response_model_by_alias=True,
)
async def receipts_get_receipt_history(
    id: StrictStr = Path(..., description=""),
) -> List[FlowHistoryEntry]:
    if not BaseReceiptsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReceiptsApi.subclasses[0]().receipts_get_receipt_history(id)


@router.put(
    "/api/receipts/{id}/task",
    responses={
        200: {"model": SampleReceipt, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["receipts"],
    response_model_by_alias=True,
)
async def receipts_assign_task(
    id: StrictStr = Path(..., description=""),
    assign_task_request: AssignTaskRequest = Body(None, description=""),
) -> SampleReceipt:
    if not BaseReceiptsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseReceiptsApi.subclasses[0]().receipts_assign_task(id, assign_task_request)
