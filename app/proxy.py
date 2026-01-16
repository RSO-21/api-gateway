import httpx
from fastapi import Request, Response

def clean_headers(headers):
    excluded = {
        b"host",
        b"content-length",
        b"connection",
        b"origin",
        b"referer",
    }
    return [
        (k, v) for k, v in headers
        if k.lower() not in excluded
    ]

async def forward_request(request: Request, base_url: str, path: str):
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method=request.method,
            url=f"{base_url}/{path}",
            params=request.query_params,
            content=await request.body(),
            headers=clean_headers(request.headers.raw),
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers),
    )