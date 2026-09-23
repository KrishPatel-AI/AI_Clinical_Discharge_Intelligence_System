"""FastAPI application entry point."""

from fastapi import FastAPI
from pydantic import BaseModel

from backend.routers.discharge import reviews_router
from backend.routers.discharge import router as discharge_router


class HealthResponse(BaseModel):
    status: str


app = FastAPI(title="AI Clinical Discharge Intelligence System")
app.include_router(discharge_router)
app.include_router(reviews_router)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return the service health status."""
    return HealthResponse(status="ok")