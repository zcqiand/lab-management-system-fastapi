# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from lab_management_system_fastapi.models.frontend_bind_meta_frontend_bind_snapshot import FrontendBindMetaFrontendBindSnapshot


class BaseFrontendBindMetaApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseFrontendBindMetaApi.subclasses = BaseFrontendBindMetaApi.subclasses + (cls,)
    async def frontend_bind_meta_get_frontend_bind_snapshot(
        self,
    ) -> FrontendBindMetaFrontendBindSnapshot:
        ...
