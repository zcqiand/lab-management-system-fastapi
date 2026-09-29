# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import StrictStr
from typing import Any, List, Optional
from lab_management_system_fastapi.models.calculation_method import CalculationMethod
from lab_management_system_fastapi.models.create_calculation_method_request import CreateCalculationMethodRequest
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.update_calculation_method_request import UpdateCalculationMethodRequest


class BaseCalculationMethodsApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseCalculationMethodsApi.subclasses = BaseCalculationMethodsApi.subclasses + (cls,)
    async def calculation_methods_list_calculation_methods(
        self,
        inspection_object_code: Optional[StrictStr],
        inspection_parameter_code: Optional[StrictStr],
    ) -> List[CalculationMethod]:
        ...


    async def calculation_methods_create_calculation_method(
        self,
        create_calculation_method_request: CreateCalculationMethodRequest,
    ) -> CalculationMethod:
        ...


    async def calculation_methods_get_calculation_method(
        self,
        inspectionObjectCode: StrictStr,
        inspectionParameterCode: StrictStr,
    ) -> CalculationMethod:
        ...


    async def calculation_methods_update_calculation_method(
        self,
        inspectionObjectCode: StrictStr,
        inspectionParameterCode: StrictStr,
        update_calculation_method_request: UpdateCalculationMethodRequest,
    ) -> CalculationMethod:
        ...


    async def calculation_methods_delete_calculation_method(
        self,
        inspectionObjectCode: StrictStr,
        inspectionParameterCode: StrictStr,
    ) -> None:
        ...
