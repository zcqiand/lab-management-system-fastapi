# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

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


class BaseReceiptsApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseReceiptsApi.subclasses = BaseReceiptsApi.subclasses + (cls,)
    async def receipts_list_receipts(
        self,
        page: Optional[StrictInt],
        page_size: Optional[StrictInt],
        keyword: Optional[StrictStr],
        contract_id: Optional[StrictStr],
        flow_status: Optional[FlowStatus],
        filter: Optional[StrictStr],
    ) -> ReceiptsListReceipts200Response:
        ...


    async def receipts_create_receipt(
        self,
        create_sample_receipt_request: CreateSampleReceiptRequest,
    ) -> SampleReceipt:
        ...


    async def receipts_act_flow_approve(
        self,
        flow_action_request: FlowActionRequest,
    ) -> List[FlowActionResult]:
        ...


    async def receipts_act_flow_archived(
        self,
        flow_action_request: FlowActionRequest,
    ) -> List[FlowActionResult]:
        ...


    async def receipts_act_flow_assigning(
        self,
        flow_action_request: FlowActionRequest,
    ) -> List[FlowActionResult]:
        ...


    async def receipts_act_flow_data_entry(
        self,
        flow_action_request: FlowActionRequest,
    ) -> List[FlowActionResult]:
        ...


    async def receipts_act_flow_issuance(
        self,
        flow_action_request: FlowActionRequest,
    ) -> List[FlowActionResult]:
        ...


    async def receipts_act_flow_receiving(
        self,
        flow_action_request: FlowActionRequest,
    ) -> List[FlowActionResult]:
        ...


    async def receipts_act_flow_review(
        self,
        flow_action_request: FlowActionRequest,
    ) -> List[FlowActionResult]:
        ...


    async def receipts_get_receipt(
        self,
        id: StrictStr,
    ) -> SampleReceipt:
        ...


    async def receipts_update_receipt(
        self,
        id: StrictStr,
        update_sample_receipt_request: UpdateSampleReceiptRequest,
    ) -> SampleReceipt:
        ...


    async def receipts_delete_receipt(
        self,
        id: StrictStr,
    ) -> None:
        ...


    async def receipts_get_receipt_history(
        self,
        id: StrictStr,
    ) -> List[FlowHistoryEntry]:
        ...


    async def receipts_assign_task(
        self,
        id: StrictStr,
        assign_task_request: AssignTaskRequest,
    ) -> SampleReceipt:
        ...
