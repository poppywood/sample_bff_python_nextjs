from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, status
from pydantic import BaseModel, Field
from redis.asyncio import Redis

from service_common.auth import AuthenticatedUser, require_authenticated_user

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")
ORDER_IDS_KEY = "service-a:orders:next-id"
ORDERS_LIST_KEY = "service-a:orders"


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = Redis.from_url(REDIS_URL, decode_responses=True)
    await redis.ping()
    app.state.redis = redis
    try:
        yield
    finally:
        await redis.aclose()


app = FastAPI(
    title="service-a",
    description="Sample downstream service that verifies BFF-issued JWTs and stores demo orders in Redis.",
    lifespan=lifespan,
)


class OrderCreate(BaseModel):
    item: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=1, le=1000)


class Order(BaseModel):
    id: int
    item: str
    quantity: int
    created_by: str


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/orders", response_model=list[Order])
async def list_orders(
    user: AuthenticatedUser = Depends(require_authenticated_user),
    redis: Redis = Depends(get_redis),
) -> list[Order]:
    _ = user
    payloads = await redis.lrange(ORDERS_LIST_KEY, 0, -1)
    return [Order(**json.loads(payload)) for payload in payloads]


@app.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    user: AuthenticatedUser = Depends(require_authenticated_user),
    redis: Redis = Depends(get_redis),
) -> Order:
    order = {
        "id": await redis.incr(ORDER_IDS_KEY),
        "item": payload.item,
        "quantity": payload.quantity,
        "created_by": user.email or user.sub,
    }
    await redis.rpush(ORDERS_LIST_KEY, json.dumps(order))
    return Order(**order)
