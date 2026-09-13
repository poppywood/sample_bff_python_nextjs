from __future__ import annotations

import asyncio
from itertools import count

from fastapi import Depends, FastAPI, status
from pydantic import BaseModel, Field

from .auth import AuthenticatedUser, require_authenticated_user

app = FastAPI(title="service-a")
_order_ids = count(1)
_orders: list[dict[str, object]] = []
_orders_lock = asyncio.Lock()


class OrderCreate(BaseModel):
    item: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=1, le=1000)


class Order(BaseModel):
    id: int
    item: str
    quantity: int
    created_by: str


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/orders", response_model=list[Order])
async def list_orders(user: AuthenticatedUser = Depends(require_authenticated_user)) -> list[Order]:
    _ = user
    async with _orders_lock:
        snapshot = [Order(**order) for order in _orders]
    return snapshot


@app.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    user: AuthenticatedUser = Depends(require_authenticated_user),
) -> Order:
    async with _orders_lock:
        order = {
            "id": next(_order_ids),
            "item": payload.item,
            "quantity": payload.quantity,
            "created_by": user.email or user.sub,
        }
        _orders.append(order)
    return Order(**order)
