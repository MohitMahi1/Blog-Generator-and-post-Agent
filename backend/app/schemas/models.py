from __future__ import annotations
from typing import List, Optional, Literal, Annotated
from pydantic import BaseModel, Field
import operator
from typing_extensions import TypedDict

# Define our project Schemas

class Task(BaseModel):
    id: int
    title: str
    goal: str = Field(..., description="One sentence describing what the reader should do/understand.")
    bullets: List[str] = Field(..., min_length=3, max_length=6, description="3–6 concrete, non-overlapping subpoints to cover in this section.",)
    target_words: int = Field(..., description="Target words (50–100).")
    tags: List[str] = Field(default_factory=list)
    requires_research: bool = False
    requires_citations: bool = False
    requires_code: bool = False

class Plan(BaseModel):
    blog_title: str
    audience: str
    tone: str
    blog_kind: Literal["explainer", "tutorial", "news_roundup", "comparison", "system_design"] = "explainer"
    constraints: List[str] = Field(default_factory=list)
    tasks: List[Task]

class EvidenceItem(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None
    snippet: Optional[str] = None
    source: Optional[str] = None

class RouterDecision(BaseModel):
    needs_research: bool
    mode: Literal["closed_book", "hybrid", "open_book"]
    reason: str
    queries: List[str] = Field(default_factory=list)
    max_results_per_query: int = Field(5)

class EvidencePack(BaseModel):
    evidence: List[EvidenceItem] = Field(default_factory=list)

class ImageSpec(BaseModel):
    placeholder: str
    filename: str
    alt: str
    caption: str
    prompt: str
    # Plain strings (not Literal) on purpose: the LLM occasionally emits an
    # arbitrary size like "1566x1536", which used to crash structured output.
    # decide_images normalizes these to known values before use.
    size: str = "1024x1024"
    quality: str = "medium"

class GlobalImagePlan(BaseModel):
    md_with_placeholders: str
    images: List[ImageSpec] = Field(default_factory=list)

# Request / Response for API
class GenerateRequest(BaseModel):
    topic: str
    as_of: Optional[str] = None 
    session_id: Optional[str] = None

class GenerateResponse(BaseModel):
    blog_id: Optional[str] = None
    session_id: Optional[str] = None
    blog_title: str
    final_markdown: str
    mode: str
    needs_research: bool
    sections_count: int

    plan: Optional[Plan] = None
    queries: List[str] = []
    evidence: List[EvidenceItem] = []
    image_specs: List[ImageSpec] = []
    logs: List[str] = []

class BlogListItem(BaseModel):
    blog_id: str
    blog_title: str
    created_at: str
    session_id: str

class BlogListResponse(BaseModel):
    blogs: List[BlogListItem] = []