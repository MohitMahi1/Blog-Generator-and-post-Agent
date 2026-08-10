from fastapi import APIRouter, HTTPException
from app.schemas.models import GenerateRequest, GenerateResponse, BlogListResponse, BlogListItem
from app.services.blog_service import generate_blog
from app.core import database

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

@router.get("/blogs/{session_id}", response_model=BlogListResponse)
def get_session_blogs(session_id: str):
    try:
        blogs = database.get_blogs_by_session(session_id)
        return BlogListResponse(blogs=[BlogListItem(**b) for b in blogs])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/blog/{blog_id}", response_model=GenerateResponse)
def get_blog(blog_id: str):
    blog = database.get_blog_by_id(blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found or expired.")
    return GenerateResponse(**blog)

@router.delete("/blog/{blog_id}")
def delete_blog(blog_id: str):
    deleted = database.delete_blog_by_id(blog_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Blog not found or could not be deleted.")
    return {"status": "deleted", "blog_id": blog_id}