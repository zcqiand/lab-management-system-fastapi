# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from lab_management_system_fastapi.apis.frontend_bind_meta_api_base import BaseFrontendBindMetaApi
import lab_management_system_fastapi.impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from lab_management_system_fastapi.models.extra_models import TokenModel  # noqa: F401
from lab_management_system_fastapi.models.frontend_bind_meta_frontend_bind_snapshot import FrontendBindMetaFrontendBindSnapshot


router = APIRouter()

ns_pkg = lab_management_system_fastapi.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.get(
    "/api/_frontend-bind/snapshot",
    responses={
        200: {"model": FrontendBindMetaFrontendBindSnapshot, "description": "The request has succeeded."},
    },
    tags=["frontend-bind-meta"],
    response_model_by_alias=True,
)
async def frontend_bind_meta_get_frontend_bind_snapshot(
) -> FrontendBindMetaFrontendBindSnapshot:
    if not BaseFrontendBindMetaApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseFrontendBindMetaApi.subclasses[0]().frontend_bind_meta_get_frontend_bind_snapshot()
