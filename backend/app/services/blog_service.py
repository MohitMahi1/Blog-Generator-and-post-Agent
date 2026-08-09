from datetime import date
from app.graph.build import app_graph
from app.schemas.models import GenerateRequest, GenerateResponse

"""
    Its entire job is 
        1) translate GenerateRequest → graph's internal State shape with every key safely defaulted, 
        2) run the graph once synchronously, 
        3) translate the graph's final State → GenerateResponse with defensive fallbacks at every field.
"""


def generate_blog(request: GenerateRequest) -> GenerateResponse:
    as_of = request.as_of or date.today().isoformat()
    
    # explicitly initializing every single field our State
    initial_state = {
        "topic": request.topic,
        "as_of": as_of,
        "mode": "",
        "needs_research": False,
        "queries": [],
        "evidence": [],
        "plan": None,
        "recency_days": 3650,
        "sections": [],
        "merged_md": "",
        "md_with_placeholders": "",
        "image_specs": [],
        "final": "",
    }
    
    # invocation of graph
    result = app_graph.invoke(initial_state)

    plan = result.get("plan")
    # getting response
    return GenerateResponse(
        blog_title=plan.blog_title if plan else "Untitled",
        final_markdown=result.get("final", ""),
        mode=result.get("mode", "closed_book"),
        needs_research=result.get("needs_research", False),
        sections_count=len(result.get("sections", [])),
    )