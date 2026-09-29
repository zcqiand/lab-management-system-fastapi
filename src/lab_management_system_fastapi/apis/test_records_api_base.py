# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import StrictInt, StrictStr
from typing import Any, Optional
from lab_management_system_fastapi.models.create_test_record_request import CreateTestRecordRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.test_record import TestRecord
from lab_management_system_fastapi.models.test_records_list_test_records200_response import TestRecordsListTestRecords200Response
from lab_management_system_fastapi.models.test_records_set_verdict_request import TestRecordsSetVerdictRequest
from lab_management_system_fastapi.models.update_test_record_request import UpdateTestRecordRequest


class BaseTestRecordsApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseTestRecordsApi.subclasses = BaseTestRecordsApi.subclasses + (cls,)
    async def test_records_list_test_records(
        self,
        page: Optional[StrictInt],
        page_size: Optional[StrictInt],
        sample_id: Optional[StrictStr],
        parameter_code: Optional[StrictStr],
    ) -> TestRecordsListTestRecords200Response:
        ...


    async def test_records_create_test_record(
        self,
        create_test_record_request: CreateTestRecordRequest,
    ) -> TestRecord:
        ...


    async def test_records_get_test_record(
        self,
        id: StrictStr,
    ) -> TestRecord:
        ...


    async def test_records_update_test_record(
        self,
        id: StrictStr,
        update_test_record_request: UpdateTestRecordRequest,
    ) -> TestRecord:
        ...


    async def test_records_delete_test_record(
        self,
        id: StrictStr,
    ) -> None:
        ...


    async def test_records_set_verdict(
        self,
        id: StrictStr,
        test_records_set_verdict_request: TestRecordsSetVerdictRequest,
    ) -> TestRecord:
        ...
