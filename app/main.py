import os
import httpx
from fastapi import FastAPI, Request, Response
from strawberry.fastapi import GraphQLRouter
from app.schemas import schema 
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.middleware.cors import CORSMiddleware

from app.services.users import router as users_router
from app.services.partners import router as partners_router
from app.services.offer import router as offer_router
from app.services.auth import router as auth_router
from app.services.order import router as order_router
from app.services.payment import router as payment_router
from app.services.notification import router as notification_router
from app.services.review import router as review_router
from app.schemas import schema  # tvoj Strawberry schema

# -----------------------
# FastAPI app
# -----------------------
app = FastAPI(title="API Gateway")

# -----------------------
# Middleware
# -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",  # Angular dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(partners_router)
app.include_router(offer_router)
app.include_router(auth_router)
app.include_router(order_router)
app.include_router(payment_router)
app.include_router(notification_router)
app.include_router(review_router)

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
        "response": response,
        "http_client": request.app.state.http_client,
    }

graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/graphql")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "api-gateway"}

@app.get("/")
def read_root():
    return {"status": "running", "endpoints": ["/graphql"]}