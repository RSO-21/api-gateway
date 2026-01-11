from fastapi import APIRouter, Request
from app.proxy import forward_request

router = APIRouter(prefix="/orders")

ORDER_SERVICE_URL = "http://order-service:8000"

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def order_proxy(path: str, request: Request):
    return await forward_request(request, ORDER_SERVICE_URL, path)