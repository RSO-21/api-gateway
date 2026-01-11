import httpx
from fastapi import Request, Response

async def forward_request(request: Request, base_url: str, path: str):
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            request.method,
            f"{base_url}/{path}",
            headers=request.headers.raw,
            params=request.query_params,
            content=await request.body()
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=resp.headers
    )