# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import StrictStr
from typing import Optional
from lab_management_system_fastapi.models.dashboard_stats import DashboardStats
from lab_management_system_fastapi.models.error_response import ErrorResponse
from lab_management_system_fastapi.models.summary_data import SummaryData


class BaseSummaryApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseSummaryApi.subclasses = BaseSummaryApi.subclasses + (cls,)
    async def summary_get_report_summary(
        self,
        category_code: Optional[StrictStr],
        date_from: Optional[StrictStr],
        date_to: Optional[StrictStr],
    ) -> SummaryData:
        ...


    async def summary_get_dashboard_stats(
        self,
    ) -> DashboardStats:
        ...
