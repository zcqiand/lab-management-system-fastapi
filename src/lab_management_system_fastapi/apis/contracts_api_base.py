# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import StrictInt, StrictStr
from typing import Any, Optional
from lab_management_system_fastapi.models.contract import Contract
from lab_management_system_fastapi.models.contract_status import ContractStatus
from lab_management_system_fastapi.models.contracts_list_contracts200_response import ContractsListContracts200Response
from lab_management_system_fastapi.models.create_contract_request import CreateContractRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.update_contract_request import UpdateContractRequest


class BaseContractsApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseContractsApi.subclasses = BaseContractsApi.subclasses + (cls,)
    async def contracts_list_contracts(
        self,
        page: Optional[StrictInt],
        page_size: Optional[StrictInt],
        keyword: Optional[StrictStr],
        status: Optional[ContractStatus],
    ) -> ContractsListContracts200Response:
        ...


    async def contracts_create_contract(
        self,
        create_contract_request: CreateContractRequest,
    ) -> Contract:
        ...


    async def contracts_get_contract(
        self,
        id: StrictStr,
    ) -> Contract:
        ...


    async def contracts_update_contract(
        self,
        id: StrictStr,
        update_contract_request: UpdateContractRequest,
    ) -> Contract:
        ...


    async def contracts_delete_contract(
        self,
        id: StrictStr,
    ) -> None:
        ...
