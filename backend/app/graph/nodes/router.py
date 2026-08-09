from datetime import date
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm import llm
from app.schemas.models import RouterDecision
from app.graph.state import State

"""
    The router node tells the llm, for the given topic
    we need search in internet or not. 
    means if topic is recently, then llm did not train upon them
    so we have to search on internet and help to generate blog.
"""

# Router prompt
ROUTER_SYSTEM = """You are a routing module for a technical blog planner.

Decide whether web research is needed BEFORE planning.

Modes:
- closed_book (needs_research=false): evergreen concepts.
- hybrid (needs_research=true): evergreen + needs up-to-date examples/tools/models.
- open_book (needs_research=true): volatile weekly/news/"latest"/pricing/policy.

If needs_research=true:
- Output 3–10 high-signal, scoped queries.
- For open_book weekly roundup, include queries reflecting last 7 days.
"""

# Router node -: decide need search or not
def router_node(state: State) -> dict:
    decider = llm.with_structured_output(RouterDecision)
    decision = decider.invoke(
        [
            SystemMessage(content=ROUTER_SYSTEM),
            HumanMessage(content=f"Topic: {state['topic']}\nAs-of date: {state['as_of']}"),
        ]
    )

    if decision.mode == "open_book": #Latest/news/volatile information
        recency_days = 7
    elif decision.mode == "hybrid": # Evergreen + recent information
        recency_days = 45
    else: # Stable/evergreen knowledge
        recency_days = 3650

    return {
        "needs_research": decision.needs_research,
        "mode": decision.mode,
        "queries": decision.queries,
        "recency_days": recency_days,
    }

def route_next(state: State) -> str:
    return "research" if state["needs_research"] else "orchestrator"