from fastapi import APIRouter, Request
from app.proxy import forward_request

router = APIRouter(prefix="/reviews")

REVIEW_SERVICE_URL = "http://review-service:8000"

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def review_proxy(path: str, request: Request):
    return await forward_request(request, REVIEW_SERVICE_URL, path)