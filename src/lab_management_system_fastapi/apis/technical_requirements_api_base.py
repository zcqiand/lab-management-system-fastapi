# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import StrictStr
from typing import Any, List, Optional
from lab_management_system_fastapi.models.create_technical_requirement_request import CreateTechnicalRequirementRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.requirement_verification_status import RequirementVerificationStatus
from lab_management_system_fastapi.models.technical_requirement import TechnicalRequirement
from lab_management_system_fastapi.models.update_technical_requirement_request import UpdateTechnicalRequirementRequest


class BaseTechnicalRequirementsApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseTechnicalRequirementsApi.subclasses = BaseTechnicalRequirementsApi.subclasses + (cls,)
    async def technical_requirements_list_technical_requirements(
        self,
        inspection_object_code: Optional[StrictStr],
        inspection_parameter_code: Optional[StrictStr],
        judgment_standard_code: Optional[StrictStr],
        verification_status: Optional[RequirementVerificationStatus],
    ) -> List[TechnicalRequirement]:
        ...


    async def technical_requirements_create_technical_requirement(
        self,
        create_technical_requirement_request: CreateTechnicalRequirementRequest,
    ) -> TechnicalRequirement:
        ...


    async def technical_requirements_get_technical_requirement(
        self,
        inspectionObjectCode: StrictStr,
        inspectionParameterCode: StrictStr,
        judgmentStandardCode: StrictStr,
    ) -> TechnicalRequirement:
        ...


    async def technical_requirements_update_technical_requirement(
        self,
        inspectionObjectCode: StrictStr,
        inspectionParameterCode: StrictStr,
        judgmentStandardCode: StrictStr,
        update_technical_requirement_request: UpdateTechnicalRequirementRequest,
    ) -> TechnicalRequirement:
        ...


    async def technical_requirements_delete_technical_requirement(
        self,
        inspectionObjectCode: StrictStr,
        inspectionParameterCode: StrictStr,
        judgmentStandardCode: StrictStr,
    ) -> None:
        ...
