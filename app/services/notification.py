from fastapi import APIRouter, Request
from app.proxy import forward_request

router = APIRouter(prefix="/notifications")

NOTIFICATION_SERVICE_URL = "http://notification-service:8000"

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def notification_proxy(path: str, request: Request):
    return await forward_request(request, NOTIFICATION_SERVICE_URL, path)