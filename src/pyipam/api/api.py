from fastapi import APIRouter

from pyipam.api import ipaddress, subnet

api_router = APIRouter()
api_router.include_router(subnet.router, tags=["subnets"])
api_router.include_router(ipaddress.router, tags=["ipaddresses"])
