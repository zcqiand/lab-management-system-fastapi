# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import StrictInt, StrictStr
from typing import Any, Optional
from lab_management_system_fastapi.models.create_sample_request import CreateSampleRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.sample import Sample
from lab_management_system_fastapi.models.samples_list_samples200_response import SamplesListSamples200Response
from lab_management_system_fastapi.models.update_sample_ext_request import UpdateSampleExtRequest
from lab_management_system_fastapi.models.update_sample_request import UpdateSampleRequest


class BaseSamplesApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseSamplesApi.subclasses = BaseSamplesApi.subclasses + (cls,)
    async def samples_list_samples(
        self,
        page: Optional[StrictInt],
        page_size: Optional[StrictInt],
        receipt_id: Optional[StrictStr],
        keyword: Optional[StrictStr],
    ) -> SamplesListSamples200Response:
        ...


    async def samples_create_sample(
        self,
        create_sample_request: CreateSampleRequest,
    ) -> Sample:
        ...


    async def samples_get_sample(
        self,
        id: StrictStr,
    ) -> Sample:
        ...


    async def samples_update_sample(
        self,
        id: StrictStr,
        update_sample_request: UpdateSampleRequest,
    ) -> Sample:
        ...


    async def samples_delete_sample(
        self,
        id: StrictStr,
    ) -> None:
        ...


    async def samples_update_sample_ext(
        self,
        id: StrictStr,
        update_sample_ext_request: UpdateSampleExtRequest,
    ) -> Sample:
        ...
