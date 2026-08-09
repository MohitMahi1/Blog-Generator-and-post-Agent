from fastapi import APIRouter, HTTPException
from app.schemas.models import GenerateRequest, GenerateResponse
from app.services.blog_service import generate_blog

router = APIRouter(prefix="/api/v1", tags=["Blog Agent"])

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest):
    try:
        return generate_blog(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))