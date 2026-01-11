from fastapi import APIRouter, Request
from app.proxy import forward_request

router = APIRouter(prefix="/users")

USERS_SERVICE_URL = "http://user-service:8000"

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def users_proxy(path: str, request: Request):
    return await forward_request(request, USERS_SERVICE_URL, path)
