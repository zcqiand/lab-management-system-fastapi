# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from lab_management_system_fastapi.apis.contracts_api_base import BaseContractsApi
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
from lab_management_system_fastapi.models.contract import Contract
from lab_management_system_fastapi.models.contract_status import ContractStatus
from lab_management_system_fastapi.models.contracts_list_contracts200_response import ContractsListContracts200Response
from lab_management_system_fastapi.models.create_contract_request import CreateContractRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.update_contract_request import UpdateContractRequest


router = APIRouter()

ns_pkg = lab_management_system_fastapi.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/contracts",
    responses={
        200: {"model": ContractsListContracts200Response, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["contracts"],
    response_model_by_alias=True,
)
async def contracts_list_contracts(
    page: Optional[StrictInt] = Query(None, description="", alias="page"),
    page_size: Optional[StrictInt] = Query(None, description="", alias="pageSize"),
    keyword: Optional[StrictStr] = Query(None, description="", alias="keyword"),
    status: Optional[ContractStatus] = Query(None, description="", alias="status"),
) -> ContractsListContracts200Response:
    if not BaseContractsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseContractsApi.subclasses[0]().contracts_list_contracts(page, page_size, keyword, status)


@router.post(
    "/api/contracts",
    responses={
        200: {"model": Contract, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["contracts"],
    response_model_by_alias=True,
)
async def contracts_create_contract(
    create_contract_request: CreateContractRequest = Body(None, description=""),
) -> Contract:
    if not BaseContractsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseContractsApi.subclasses[0]().contracts_create_contract(create_contract_request)


@router.get(
    "/api/contracts/{id}",
    responses={
        200: {"model": Contract, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["contracts"],
    response_model_by_alias=True,
)
async def contracts_get_contract(
    id: StrictStr = Path(..., description=""),
) -> Contract:
    if not BaseContractsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseContractsApi.subclasses[0]().contracts_get_contract(id)


@router.put(
    "/api/contracts/{id}",
    responses={
        200: {"model": Contract, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["contracts"],
    response_model_by_alias=True,
)
async def contracts_update_contract(
    id: StrictStr = Path(..., description=""),
    update_contract_request: UpdateContractRequest = Body(None, description=""),
) -> Contract:
    if not BaseContractsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseContractsApi.subclasses[0]().contracts_update_contract(id, update_contract_request)


@router.delete(
    "/api/contracts/{id}",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["contracts"],
    response_model_by_alias=True,
)
async def contracts_delete_contract(
    id: StrictStr = Path(..., description=""),
) -> None:
    if not BaseContractsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseContractsApi.subclasses[0]().contracts_delete_contract(id)
