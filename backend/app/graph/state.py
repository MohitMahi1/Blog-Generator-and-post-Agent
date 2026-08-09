from typing import List, Optional, Annotated
from typing_extensions import TypedDict
import operator
from app.schemas.models import Plan, EvidenceItem

# Define the state
class State(TypedDict):
    topic: str
    
    # routing / research
    mode: str
    needs_research: bool
    queries: List[str]
    evidence: List[EvidenceItem]
    plan: Optional[Plan]
    
    # recency
    as_of: str
    recency_days: int
    
    # worker
    sections: Annotated[List[tuple[int, str]], operator.add]
    
    # reducer/image
    merged_md: str
    md_with_placeholders: str
    image_specs: List[dict]
    
    # final answer
    final: str