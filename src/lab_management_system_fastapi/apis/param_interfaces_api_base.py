# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import StrictInt, StrictStr
from typing import Any, Optional
from lab_management_system_fastapi.models.create_param_interface_request import CreateParamInterfaceRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.param_interface import ParamInterface
from lab_management_system_fastapi.models.param_interface_link import ParamInterfaceLink
from lab_management_system_fastapi.models.param_interfaces_list_param_interface_links200_response import ParamInterfacesListParamInterfaceLinks200Response
from lab_management_system_fastapi.models.param_interfaces_list_param_interfaces200_response import ParamInterfacesListParamInterfaces200Response
from lab_management_system_fastapi.models.param_interfaces_unlink_param_interface_request import ParamInterfacesUnlinkParamInterfaceRequest
from lab_management_system_fastapi.models.update_param_interface_request import UpdateParamInterfaceRequest


class BaseParamInterfacesApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseParamInterfacesApi.subclasses = BaseParamInterfacesApi.subclasses + (cls,)
    async def param_interfaces_list_param_interfaces(
        self,
        page: Optional[StrictInt],
        page_size: Optional[StrictInt],
        keyword: Optional[StrictStr],
    ) -> ParamInterfacesListParamInterfaces200Response:
        ...


    async def param_interfaces_create_param_interface(
        self,
        create_param_interface_request: CreateParamInterfaceRequest,
    ) -> ParamInterface:
        ...


    async def param_interfaces_list_param_interface_links(
        self,
        inspection_parameter_code: Optional[StrictStr],
        param_interface_code: Optional[StrictStr],
    ) -> ParamInterfacesListParamInterfaceLinks200Response:
        ...


    async def param_interfaces_link_param_interface(
        self,
        param_interface_link: ParamInterfaceLink,
    ) -> None:
        ...


    async def param_interfaces_unlink_param_interface(
        self,
        param_interfaces_unlink_param_interface_request: ParamInterfacesUnlinkParamInterfaceRequest,
    ) -> None:
        ...


    async def param_interfaces_get_param_interface(
        self,
        code: StrictStr,
    ) -> ParamInterface:
        ...


    async def param_interfaces_update_param_interface(
        self,
        code: StrictStr,
        update_param_interface_request: UpdateParamInterfaceRequest,
    ) -> ParamInterface:
        ...


    async def param_interfaces_delete_param_interface(
        self,
        code: StrictStr,
    ) -> None:
        ...
