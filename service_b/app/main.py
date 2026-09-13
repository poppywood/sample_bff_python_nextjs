from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, status
from pydantic import BaseModel, Field
from redis.asyncio import Redis

from .auth import AuthenticatedUser, require_authenticated_user

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/2")
NOTE_IDS_KEY = "service-b:notes:next-id"
NOTES_LIST_KEY = "service-b:notes"


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
    title="service-b",
    description="Second demo downstream service that verifies BFF-issued JWTs and stores demo notes in Redis.",
    lifespan=lifespan,
)


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=280)


class Note(BaseModel):
    id: int
    title: str
    content: str
    created_by: str


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/notes", response_model=list[Note])
async def list_notes(
    user: AuthenticatedUser = Depends(require_authenticated_user),
    redis: Redis = Depends(get_redis),
) -> list[Note]:
    _ = user
    payloads = await redis.lrange(NOTES_LIST_KEY, 0, -1)
    return [Note(**json.loads(payload)) for payload in payloads]


@app.post("/notes", response_model=Note, status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: NoteCreate,
    user: AuthenticatedUser = Depends(require_authenticated_user),
    redis: Redis = Depends(get_redis),
) -> Note:
    note = {
        "id": await redis.incr(NOTE_IDS_KEY),
        "title": payload.title,
        "content": payload.content,
        "created_by": user.email or user.sub,
    }
    await redis.rpush(NOTES_LIST_KEY, json.dumps(note))
    return Note(**note)
