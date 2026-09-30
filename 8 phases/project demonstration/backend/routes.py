from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ai_core.gemini_generator import (
    GeminiDocumentGenerator,
    GeminiGenerationError,
)
from config import get_settings


router = APIRouter(
    prefix="/api",
    tags=["LegalEase"],
)


class DocumentRequest(BaseModel):
    document_type: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )
    parties: str = Field(
        ...,
        min_length=2,
        max_length=5000,
    )
    terms: str = Field(
        ...,
        min_length=2,
        max_length=10000,
    )
    effective_date: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )


class DocumentResponse(BaseModel):
    document_type: str
    effective_date: str
    content: str
    model: str


@router.get("/formats")
def get_formats():
    return {
        "formats": [
            "Employment Agreement",
            "Lease Agreement",
            "Non-Disclosure Agreement",
            "Service Agreement",
            "Freelance Agreement",
            "Consulting Agreement",
            "Partnership Agreement",
            "Custom Legal Document",
        ]
    }


@router.post("/generate", response_model=DocumentResponse)
def generate_document(request: DocumentRequest):
    settings = get_settings()

    generator = GeminiDocumentGenerator(settings)

    try:
        content = generator.generate_document(
            document_type=request.document_type,
            parties=request.parties,
            terms=request.terms,
            effective_date=request.effective_date,
        )

        return DocumentResponse(
            document_type=request.document_type,
            effective_date=request.effective_date,
            content=content,
            model=settings.gemini_model,
        )

    except GeminiGenerationError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {exc}",
        ) from exc