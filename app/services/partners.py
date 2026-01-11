from fastapi import APIRouter, Request
from app.proxy import forward_request

router = APIRouter(prefix="/partners")

PARTNERS_SERVICE_URL = "http://partner-service:8000"

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def partners_proxy(path: str, request: Request):
    return await forward_request(request, PARTNERS_SERVICE_URL, path)