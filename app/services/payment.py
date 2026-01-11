from fastapi import APIRouter, Request
from app.proxy import forward_request

router = APIRouter(prefix="/payments")

PAYMENT_SERVICE_URL = "http://payment-service:8000"

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def payment_proxy(path: str, request: Request):
    return await forward_request(request, PAYMENT_SERVICE_URL, path)