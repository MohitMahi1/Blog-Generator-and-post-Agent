from datetime import date
from typing import List
from app.graph.build import app_graph
from app.schemas.models import GenerateRequest, GenerateResponse, Plan, EvidenceItem, ImageSpec

"""
    Its entire job is 
        1) translate GenerateRequest → graph's internal State shape with every key safely defaulted, 
        2) run the graph once synchronously, 
        3) translate the graph's final State → GenerateResponse with defensive fallbacks at every field.
"""


def generate_blog(request: GenerateRequest) -> GenerateResponse:
    as_of = request.as_of or date.today().isoformat()

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

    logs: List[str] = []
    logs.append(f"Starting generation for topic: {request.topic}")

    # ---------- Collect progress using stream ----------
    final_state = None

    try:
        for event in app_graph.stream(initial_state, stream_mode="updates"):
            # event is usually { "node_name": { ... partial state ... } }
            if isinstance(event, dict):
                for node_name, update in event.items():
                    logs.append(f"➡️ Node finished: {node_name}")

                    if node_name == "router":
                        mode = update.get("mode")
                        needs = update.get("needs_research")
                        logs.append(f"   Router decided → mode={mode}, needs_research={needs}")

                    elif node_name == "research":
                        ev_count = len(update.get("evidence", []) or [])
                        logs.append(f"   Research collected {ev_count} evidence items")

                    elif node_name == "orchestrator":
                        plan = update.get("plan")
                        if plan:
                            task_count = len(plan.tasks) if hasattr(plan, "tasks") else 0
                            logs.append(f"   Orchestrator created plan with {task_count} tasks")

                    elif node_name == "worker":
                        logs.append("   Worker finished one section")

                    elif node_name == "reducer":
                        logs.append("   Reducer (merge + images) finished")

        # Get the final complete state
        final_state = app_graph.invoke(initial_state)

    except Exception as e:
        logs.append(f"❌ Error during graph execution: {str(e)}")
        raise e

    if not final_state:
        final_state = app_graph.invoke(initial_state)

    plan: Plan | None = final_state.get("plan")
    evidence_raw = final_state.get("evidence", []) or []
    image_specs_raw = final_state.get("image_specs", []) or []

    # Convert evidence to proper objects if needed
    evidence: List[EvidenceItem] = []
    for e in evidence_raw:
        if isinstance(e, EvidenceItem):
            evidence.append(e)
        elif isinstance(e, dict):
            evidence.append(EvidenceItem(**e))

    image_specs: List[ImageSpec] = []
    for img in image_specs_raw:
        if isinstance(img, ImageSpec):
            image_specs.append(img)
        elif isinstance(img, dict):
            try:
                image_specs.append(ImageSpec(**img))
            except Exception:
                pass

    logs.append("✅ Generation completed")

    return GenerateResponse(
        blog_title=plan.blog_title if plan else "Untitled",
        final_markdown=final_state.get("final", ""),
        mode=final_state.get("mode", "closed_book"),
        needs_research=final_state.get("needs_research", False),
        sections_count=len(final_state.get("sections", [])),
        plan=plan,
        evidence=evidence,
        image_specs=image_specs,
        logs=logs,
    )