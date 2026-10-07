"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import get_allowed_origins
from backend.db import init_db
from backend.routers.discharge import reviews_router
from backend.routers.discharge import router as discharge_router


class HealthResponse(BaseModel):
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    yield


app = FastAPI(
    title="AI Clinical Discharge Intelligence System",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(discharge_router)
app.include_router(reviews_router)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return the service health status."""
    return HealthResponse(status="ok")