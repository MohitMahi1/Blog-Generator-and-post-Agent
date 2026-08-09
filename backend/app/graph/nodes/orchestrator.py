from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm import llm
from app.schemas.models import Plan
from app.graph.state import State

"""
    Then the topic and all research sources(IF research needed then)
    are come to orchestrator node and then this node plan -:
        How to write
        What's the title 
        How many section are there in this blog etc
"""


# Orchestrator prompt
ORCH_SYSTEM = """You are a senior technical writer and developer advocate.
Produce a highly actionable outline for a technical blog post.

Requirements:
- 5–9 tasks, each with goal + 3–6 bullets + target_words.
- Tags are flexible.

Grounding:
- closed_book: evergreen, no evidence dependence.
- hybrid: use evidence for up-to-date examples; mark those tasks requires_research=True and requires_citations=True.
- open_book: weekly/news roundup:
  - Set blog_kind="news_roundup"
  - No tutorial content unless requested
  - If evidence is weak, plan should explicitly reflect that.

Output must match Plan schema.
"""

# Orchestrator node -: Planning node
def orchestrator_node(state : State) -> dict:
    planner = llm.with_structured_output(Plan) #Planning as per Plan schema
    mode = state.get("mode", "closed_book")
    evidence = state.get("evidence", [])
    
    forced_kind = "news_roundup" if mode == "open_book" else None
    
    plan = planner.invoke(
        [
            SystemMessage(content=ORCH_SYSTEM),
            HumanMessage(
                content=(
                    f"Topic: {state['topic']}\n"
                    f"Mode: {mode}\n"
                    f"As-of: {state['as_of']} (recency_days={state['recency_days']})\n"
                    f"{'Force blog_kind=news_roundup' if forced_kind else ''}\n\n"
                    f"Evidence:\n{[e.model_dump() for e in evidence][:16]}"
                )
            ),
        ]
    )
    
    if forced_kind:
        plan.blog_kind = "news_roundup"
        
    return {"plan" : plan}