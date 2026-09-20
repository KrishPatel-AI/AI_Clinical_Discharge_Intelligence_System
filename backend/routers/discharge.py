"""Discharge-summary upload routes."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.config import get_ollama_base_url, get_ollama_model
from backend.llm.provider import LLMProvider, OllamaProvider
from backend.models.schemas import ExtractionResponse
from backend.services.extraction import extract_upload

router = APIRouter(prefix="/discharge", tags=["discharge"])


def get_llm_provider() -> LLMProvider:
    return OllamaProvider(get_ollama_base_url(), get_ollama_model())


FILE_UPLOAD = File(...)
PROVIDER_DEPENDENCY = Depends(get_llm_provider)


@router.post("/extract", response_model=ExtractionResponse)
async def extract_discharge(
    file: UploadFile = FILE_UPLOAD, provider: LLMProvider = PROVIDER_DEPENDENCY
) -> ExtractionResponse:
    try:
        extraction = await extract_upload(file, provider)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    return ExtractionResponse(
        filename=file.filename or "unknown",
        content_type=file.content_type,
        extraction=extraction,
    )