import os
import httpx
from fastapi import FastAPI, Request, Response
from strawberry.fastapi import GraphQLRouter
from app.schemas import schema 
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API Gateway")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",  # Angular dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Expose /metrics compatible with Prometheus scraping
Instrumentator().instrument(app).expose(app)

# 1. Initialize a global HTTP client for performance (reuses connections)
@app.on_event("startup")
async def startup_event():
    app.state.http_client = httpx.AsyncClient()

@app.on_event("shutdown")
async def shutdown_event():
    await app.state.http_client.aclose()

# 2. Add services to context so resolvers can use them
async def get_context(request: Request, response: Response):
    return {
        "request": request,
        "response": response, # Add this line
        "http_client": request.app.state.http_client,
    }

# When creating the schema view
schema_view = GraphQLRouter(schema, context_getter=get_context)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "api-gateway"}

graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
def read_root():
    return {"status": "running", "endpoints": ["/graphql"]}