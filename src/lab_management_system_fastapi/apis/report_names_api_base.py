# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import StrictInt, StrictStr
from typing import Any, Optional
from lab_management_system_fastapi.models.create_inspection_report_name_request import CreateInspectionReportNameRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.inspection_report_name import InspectionReportName
from lab_management_system_fastapi.models.inspection_standard_role import InspectionStandardRole
from lab_management_system_fastapi.models.object_report_name_link import ObjectReportNameLink
from lab_management_system_fastapi.models.report_name_parameter_link import ReportNameParameterLink
from lab_management_system_fastapi.models.report_name_standard_link import ReportNameStandardLink
from lab_management_system_fastapi.models.report_names_list_object_report_name_links200_response import ReportNamesListObjectReportNameLinks200Response
from lab_management_system_fastapi.models.report_names_list_report_name_parameter_links200_response import ReportNamesListReportNameParameterLinks200Response
from lab_management_system_fastapi.models.report_names_list_report_name_standard_links200_response import ReportNamesListReportNameStandardLinks200Response
from lab_management_system_fastapi.models.report_names_list_report_names200_response import ReportNamesListReportNames200Response
from lab_management_system_fastapi.models.report_names_unlink_object_report_name_request import ReportNamesUnlinkObjectReportNameRequest
from lab_management_system_fastapi.models.report_names_unlink_report_name_parameter_request import ReportNamesUnlinkReportNameParameterRequest
from lab_management_system_fastapi.models.report_names_unlink_report_name_standard_request import ReportNamesUnlinkReportNameStandardRequest
from lab_management_system_fastapi.models.update_inspection_report_name_request import UpdateInspectionReportNameRequest


class BaseReportNamesApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseReportNamesApi.subclasses = BaseReportNamesApi.subclasses + (cls,)
    async def report_names_list_report_names(
        self,
        page: Optional[StrictInt],
        page_size: Optional[StrictInt],
        keyword: Optional[StrictStr],
    ) -> ReportNamesListReportNames200Response:
        ...


    async def report_names_create_report_name(
        self,
        create_inspection_report_name_request: CreateInspectionReportNameRequest,
    ) -> InspectionReportName:
        ...


    async def report_names_list_object_report_name_links(
        self,
        inspection_object_code: Optional[StrictStr],
        report_name_code: Optional[StrictStr],
    ) -> ReportNamesListObjectReportNameLinks200Response:
        ...


    async def report_names_link_object_report_name(
        self,
        object_report_name_link: ObjectReportNameLink,
    ) -> None:
        ...


    async def report_names_unlink_object_report_name(
        self,
        report_names_unlink_object_report_name_request: ReportNamesUnlinkObjectReportNameRequest,
    ) -> None:
        ...


    async def report_names_list_report_name_parameter_links(
        self,
        report_name_code: Optional[StrictStr],
        inspection_parameter_code: Optional[StrictStr],
    ) -> ReportNamesListReportNameParameterLinks200Response:
        ...


    async def report_names_link_report_name_parameter(
        self,
        report_name_parameter_link: ReportNameParameterLink,
    ) -> None:
        ...


    async def report_names_unlink_report_name_parameter(
        self,
        report_names_unlink_report_name_parameter_request: ReportNamesUnlinkReportNameParameterRequest,
    ) -> None:
        ...


    async def report_names_list_report_name_standard_links(
        self,
        report_name_code: Optional[StrictStr],
        role: Optional[InspectionStandardRole],
    ) -> ReportNamesListReportNameStandardLinks200Response:
        ...


    async def report_names_link_report_name_standard(
        self,
        report_name_standard_link: ReportNameStandardLink,
    ) -> None:
        ...


    async def report_names_unlink_report_name_standard(
        self,
        report_names_unlink_report_name_standard_request: ReportNamesUnlinkReportNameStandardRequest,
    ) -> None:
        ...


    async def report_names_get_report_name(
        self,
        code: StrictStr,
    ) -> InspectionReportName:
        ...


    async def report_names_update_report_name(
        self,
        code: StrictStr,
        update_inspection_report_name_request: UpdateInspectionReportNameRequest,
    ) -> InspectionReportName:
        ...


    async def report_names_delete_report_name(
        self,
        code: StrictStr,
    ) -> None:
        ...
