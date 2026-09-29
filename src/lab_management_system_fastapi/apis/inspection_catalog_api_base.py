# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import StrictInt, StrictStr
from typing import Any, Optional
from lab_management_system_fastapi.models.catalog_list_brands200_response import CatalogListBrands200Response
from lab_management_system_fastapi.models.catalog_list_grades200_response import CatalogListGrades200Response
from lab_management_system_fastapi.models.catalog_list_models200_response import CatalogListModels200Response
from lab_management_system_fastapi.models.catalog_list_specs200_response import CatalogListSpecs200Response
from lab_management_system_fastapi.models.create_catalog_entry_request import CreateCatalogEntryRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.inspection_brand import InspectionBrand
from lab_management_system_fastapi.models.inspection_grade import InspectionGrade
from lab_management_system_fastapi.models.inspection_model import InspectionModel
from lab_management_system_fastapi.models.inspection_spec import InspectionSpec
from lab_management_system_fastapi.models.update_catalog_entry_request import UpdateCatalogEntryRequest


class BaseInspectionCatalogApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseInspectionCatalogApi.subclasses = BaseInspectionCatalogApi.subclasses + (cls,)
    async def catalog_list_brands(
        self,
        page: Optional[StrictInt],
        page_size: Optional[StrictInt],
        inspection_object_code: Optional[StrictStr],
        keyword: Optional[StrictStr],
    ) -> CatalogListBrands200Response:
        ...


    async def catalog_create_brand(
        self,
        create_catalog_entry_request: CreateCatalogEntryRequest,
    ) -> InspectionBrand:
        ...


    async def catalog_update_brand(
        self,
        code: StrictStr,
        update_catalog_entry_request: UpdateCatalogEntryRequest,
    ) -> InspectionBrand:
        ...


    async def catalog_delete_brand(
        self,
        code: StrictStr,
    ) -> None:
        ...


    async def catalog_list_grades(
        self,
        page: Optional[StrictInt],
        page_size: Optional[StrictInt],
        inspection_object_code: Optional[StrictStr],
        keyword: Optional[StrictStr],
    ) -> CatalogListGrades200Response:
        ...


    async def catalog_create_grade(
        self,
        create_catalog_entry_request: CreateCatalogEntryRequest,
    ) -> InspectionGrade:
        ...


    async def catalog_update_grade(
        self,
        code: StrictStr,
        update_catalog_entry_request: UpdateCatalogEntryRequest,
    ) -> InspectionGrade:
        ...


    async def catalog_delete_grade(
        self,
        code: StrictStr,
    ) -> None:
        ...


    async def catalog_list_models(
        self,
        page: Optional[StrictInt],
        page_size: Optional[StrictInt],
        inspection_object_code: Optional[StrictStr],
        keyword: Optional[StrictStr],
    ) -> CatalogListModels200Response:
        ...


    async def catalog_create_model(
        self,
        create_catalog_entry_request: CreateCatalogEntryRequest,
    ) -> InspectionModel:
        ...


    async def catalog_update_model(
        self,
        code: StrictStr,
        update_catalog_entry_request: UpdateCatalogEntryRequest,
    ) -> InspectionModel:
        ...


    async def catalog_delete_model(
        self,
        code: StrictStr,
    ) -> None:
        ...


    async def catalog_list_specs(
        self,
        page: Optional[StrictInt],
        page_size: Optional[StrictInt],
        inspection_object_code: Optional[StrictStr],
        keyword: Optional[StrictStr],
    ) -> CatalogListSpecs200Response:
        ...


    async def catalog_create_spec(
        self,
        create_catalog_entry_request: CreateCatalogEntryRequest,
    ) -> InspectionSpec:
        ...


    async def catalog_update_spec(
        self,
        code: StrictStr,
        update_catalog_entry_request: UpdateCatalogEntryRequest,
    ) -> InspectionSpec:
        ...


    async def catalog_delete_spec(
        self,
        code: StrictStr,
    ) -> None:
        ...
