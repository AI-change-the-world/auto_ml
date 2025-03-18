from fastapi import APIRouter

from base import create_response

router = APIRouter(
    prefix="/heartbeat",
    tags=["heartbeat"],
)


@router.get("/")
async def heartbeat():
    return create_response(status=200, message="OK")
