"""FastAPI application entry point."""

from fastapi import FastAPI
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


app = FastAPI(title="AI Clinical Discharge Intelligence System")


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Return the service health status."""
    return HealthResponse(status="ok")