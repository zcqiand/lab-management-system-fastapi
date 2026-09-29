# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from lab_management_system_fastapi.apis.technical_requirements_api_base import BaseTechnicalRequirementsApi
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
from lab_management_system_fastapi.models.create_technical_requirement_request import CreateTechnicalRequirementRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.requirement_verification_status import RequirementVerificationStatus
from lab_management_system_fastapi.models.technical_requirement import TechnicalRequirement
from lab_management_system_fastapi.models.update_technical_requirement_request import UpdateTechnicalRequirementRequest


router = APIRouter()

ns_pkg = lab_management_system_fastapi.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/technical-requirements",
    responses={
        200: {"model": List[TechnicalRequirement], "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["technical-requirements"],
    response_model_by_alias=True,
)
async def technical_requirements_list_technical_requirements(
    inspection_object_code: Optional[StrictStr] = Query(None, description="", alias="inspectionObjectCode"),
    inspection_parameter_code: Optional[StrictStr] = Query(None, description="", alias="inspectionParameterCode"),
    judgment_standard_code: Optional[StrictStr] = Query(None, description="", alias="judgmentStandardCode"),
    verification_status: Optional[RequirementVerificationStatus] = Query(None, description="", alias="verificationStatus"),
) -> List[TechnicalRequirement]:
    if not BaseTechnicalRequirementsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseTechnicalRequirementsApi.subclasses[0]().technical_requirements_list_technical_requirements(inspection_object_code, inspection_parameter_code, judgment_standard_code, verification_status)


@router.post(
    "/api/technical-requirements",
    responses={
        200: {"model": TechnicalRequirement, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["technical-requirements"],
    response_model_by_alias=True,
)
async def technical_requirements_create_technical_requirement(
    create_technical_requirement_request: CreateTechnicalRequirementRequest = Body(None, description=""),
) -> TechnicalRequirement:
    if not BaseTechnicalRequirementsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseTechnicalRequirementsApi.subclasses[0]().technical_requirements_create_technical_requirement(create_technical_requirement_request)


@router.get(
    "/api/technical-requirements/{inspectionObjectCode}/{inspectionParameterCode}/{judgmentStandardCode}",
    responses={
        200: {"model": TechnicalRequirement, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["technical-requirements"],
    response_model_by_alias=True,
)
async def technical_requirements_get_technical_requirement(
    inspectionObjectCode: StrictStr = Path(..., description=""),
    inspectionParameterCode: StrictStr = Path(..., description=""),
    judgmentStandardCode: StrictStr = Path(..., description=""),
) -> TechnicalRequirement:
    if not BaseTechnicalRequirementsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseTechnicalRequirementsApi.subclasses[0]().technical_requirements_get_technical_requirement(inspectionObjectCode, inspectionParameterCode, judgmentStandardCode)


@router.put(
    "/api/technical-requirements/{inspectionObjectCode}/{inspectionParameterCode}/{judgmentStandardCode}",
    responses={
        200: {"model": TechnicalRequirement, "description": "The request has succeeded."},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["technical-requirements"],
    response_model_by_alias=True,
)
async def technical_requirements_update_technical_requirement(
    inspectionObjectCode: StrictStr = Path(..., description=""),
    inspectionParameterCode: StrictStr = Path(..., description=""),
    judgmentStandardCode: StrictStr = Path(..., description=""),
    update_technical_requirement_request: UpdateTechnicalRequirementRequest = Body(None, description=""),
) -> TechnicalRequirement:
    if not BaseTechnicalRequirementsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseTechnicalRequirementsApi.subclasses[0]().technical_requirements_update_technical_requirement(inspectionObjectCode, inspectionParameterCode, judgmentStandardCode, update_technical_requirement_request)


@router.delete(
    "/api/technical-requirements/{inspectionObjectCode}/{inspectionParameterCode}/{judgmentStandardCode}",
    responses={
        204: {"description": "There is no content to send for this request, but the headers may be useful. "},
        "default": {"model": ErrorResponse, "description": "An unexpected error response."},
    },
    tags=["technical-requirements"],
    response_model_by_alias=True,
)
async def technical_requirements_delete_technical_requirement(
    inspectionObjectCode: StrictStr = Path(..., description=""),
    inspectionParameterCode: StrictStr = Path(..., description=""),
    judgmentStandardCode: StrictStr = Path(..., description=""),
) -> None:
    if not BaseTechnicalRequirementsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseTechnicalRequirementsApi.subclasses[0]().technical_requirements_delete_technical_requirement(inspectionObjectCode, inspectionParameterCode, judgmentStandardCode)
