# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

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


class BaseInspectionDictionaryApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseInspectionDictionaryApi.subclasses = BaseInspectionDictionaryApi.subclasses + (cls,)
    async def inspection_dictionary_list_object_parameter_links(
        self,
        inspection_object_code: Optional[StrictStr],
        inspection_parameter_code: Optional[StrictStr],
    ) -> InspectionDictionaryListObjectParameterLinks200Response:
        ...


    async def inspection_dictionary_link_object_parameter(
        self,
        object_parameter_link: ObjectParameterLink,
    ) -> None:
        ...


    async def inspection_dictionary_unlink_object_parameter(
        self,
        inspection_dictionary_unlink_object_parameter_request: InspectionDictionaryUnlinkObjectParameterRequest,
    ) -> None:
        ...


    async def inspection_dictionary_list_object_standard_links(
        self,
        inspection_object_code: Optional[StrictStr],
        role: Optional[InspectionStandardRole],
    ) -> InspectionDictionaryListObjectStandardLinks200Response:
        ...


    async def inspection_dictionary_link_object_standard(
        self,
        object_standard_link: ObjectStandardLink,
    ) -> None:
        ...


    async def inspection_dictionary_unlink_object_standard(
        self,
        inspection_dictionary_unlink_object_standard_request: InspectionDictionaryUnlinkObjectStandardRequest,
    ) -> None:
        ...


    async def inspection_dictionary_list_specialty_object_links(
        self,
        inspection_specialty_code: Optional[StrictStr],
    ) -> InspectionDictionaryListSpecialtyObjectLinks200Response:
        ...


    async def inspection_dictionary_link_specialty_object(
        self,
        specialty_object_link: SpecialtyObjectLink,
    ) -> None:
        ...


    async def inspection_dictionary_unlink_specialty_object(
        self,
        specialty_object_link: SpecialtyObjectLink,
    ) -> None:
        ...


    async def inspection_dictionary_list_standard_parameter_links(
        self,
        inspection_standard_code: Optional[StrictStr],
        inspection_parameter_code: Optional[StrictStr],
    ) -> InspectionDictionaryListStandardParameterLinks200Response:
        ...


    async def inspection_dictionary_link_standard_parameter(
        self,
        standard_parameter_link: StandardParameterLink,
    ) -> None:
        ...


    async def inspection_dictionary_unlink_standard_parameter(
        self,
        standard_parameter_link: StandardParameterLink,
    ) -> None:
        ...


    async def inspection_dictionary_list_objects(
        self,
        page: Optional[StrictInt],
        page_size: Optional[StrictInt],
        inspection_specialty_code: Optional[StrictStr],
        keyword: Optional[StrictStr],
    ) -> InspectionDictionaryListObjects200Response:
        ...


    async def inspection_dictionary_create_object(
        self,
        create_inspection_object_request: CreateInspectionObjectRequest,
    ) -> InspectionObject:
        ...


    async def inspection_dictionary_update_object(
        self,
        code: StrictStr,
        update_inspection_object_request: UpdateInspectionObjectRequest,
    ) -> InspectionObject:
        ...


    async def inspection_dictionary_delete_object(
        self,
        code: StrictStr,
    ) -> None:
        ...


    async def inspection_dictionary_list_parameters(
        self,
        page: Optional[StrictInt],
        page_size: Optional[StrictInt],
        keyword: Optional[StrictStr],
        source_type: Optional[InspectionParameterSourceType],
    ) -> InspectionDictionaryListParameters200Response:
        ...


    async def inspection_dictionary_create_parameter(
        self,
        create_inspection_parameter_request: CreateInspectionParameterRequest,
    ) -> InspectionParameter:
        ...


    async def inspection_dictionary_update_parameter(
        self,
        code: StrictStr,
        update_inspection_parameter_request: UpdateInspectionParameterRequest,
    ) -> InspectionParameter:
        ...


    async def inspection_dictionary_delete_parameter(
        self,
        code: StrictStr,
    ) -> None:
        ...


    async def inspection_dictionary_list_specialties(
        self,
        page: Optional[StrictInt],
        page_size: Optional[StrictInt],
        keyword: Optional[StrictStr],
    ) -> InspectionDictionaryListSpecialties200Response:
        ...


    async def inspection_dictionary_create_specialty(
        self,
        create_inspection_specialty_request: CreateInspectionSpecialtyRequest,
    ) -> InspectionSpecialty:
        ...


    async def inspection_dictionary_update_specialty(
        self,
        code: StrictStr,
        update_inspection_specialty_request: UpdateInspectionSpecialtyRequest,
    ) -> InspectionSpecialty:
        ...


    async def inspection_dictionary_delete_specialty(
        self,
        code: StrictStr,
    ) -> None:
        ...


    async def inspection_dictionary_list_standards(
        self,
        page: Optional[StrictInt],
        page_size: Optional[StrictInt],
        keyword: Optional[StrictStr],
        status: Optional[InspectionStandardStatus],
    ) -> InspectionDictionaryListStandards200Response:
        ...


    async def inspection_dictionary_create_standard(
        self,
        create_inspection_standard_request: CreateInspectionStandardRequest,
    ) -> InspectionStandard:
        ...


    async def inspection_dictionary_update_standard(
        self,
        code: StrictStr,
        update_inspection_standard_request: UpdateInspectionStandardRequest,
    ) -> InspectionStandard:
        ...


    async def inspection_dictionary_delete_standard(
        self,
        code: StrictStr,
    ) -> None:
        ...
