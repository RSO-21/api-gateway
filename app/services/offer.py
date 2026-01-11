from fastapi import APIRouter, Request
from app.proxy import forward_request

router = APIRouter(prefix="/offers")

OFFER_SERVICE_URL = "http://offer-service:8000"

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def offer_proxy(path: str, request: Request):
    return await forward_request(request, OFFER_SERVICE_URL, path)