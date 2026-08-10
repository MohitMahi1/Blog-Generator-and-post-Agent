import logging
from datetime import timedelta, date
from typing import List, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm import llm
from app.core.config import settings
from app.schemas.models import EvidenceItem, EvidencePack
from app.graph.state import State

"""
    If the topic is new then research node active and search the topic in the 
    google search by some queries and then take all the research doing then rewrite 
    our blog with sources.
"""

logger = logging.getLogger(__name__)


# website search by tavily, Where max result = 5
def _tavily_search(query: str, max_results: int = 5) -> List[dict]:
    if not settings.TAVILY_API_KEY:
        logger.warning("TAVILY_API_KEY is not set; skipping web research.")
        return []
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
        # Pass the key explicitly: the tool reads os.environ by default, which
        # doesn't see keys loaded into settings from .env.
        tool = TavilySearchResults(tavily_api_key=settings.TAVILY_API_KEY, max_results=max_results)
        results = tool.invoke({"query": query})
        out = []
        for r in results or []:
            out.append({
                "title": r.get("title") or "",
                "url": r.get("url") or "",
                "snippet": r.get("content") or r.get("snippet") or "",
                "published_at": r.get("published_date") or r.get("published_at"),
                "source": r.get("source"),
            })
        return out
    except Exception as e:
        # A silent [] here would leave open_book writers with zero grounding
        # (a hallucination risk), so make failures visible.
        logger.warning(f"Tavily search failed for query '{query}': {e}")
        return []
    
# Convert string to ISO Standard Date format
def _iso_to_date(s : Optional[str]) -> Optional[date]:
    if not s :
        return None
    try:
        return date.fromisoformat(s[:10])
    except Exception:
        return None
    
# Research prompt
RESEARCH_SYSTEM = """You are a research synthesizer.

Given raw web search results, produce EvidenceItem objects.

Rules:
- Only include items with a non-empty url.
- Prefer relevant + authoritative sources.
- Normalize published_at to ISO YYYY-MM-DD if reliably inferable; else null (do NOT guess).
- Keep snippets short.
- Deduplicate by URL.
"""

# Research node, where we go for searches
def research_node(state : State) -> dict:
    queries = (state.get("queries") or [])[:10]
    raw = []
    
    for q in queries:
        raw.extend(_tavily_search(q, max_results=8))
        
    if not raw:
        return {"evidence" : []}

    # Compact + dedupe raw results BEFORE sending to the LLM: full dicts with
    # long snippets waste tokens. Keep title/url + a short snippet.
    seen_urls = set()
    compact = []
    for r in raw:
        u = r.get("url") or ""
        if not u or u in seen_urls:
            continue
        seen_urls.add(u)
        snippet = (r.get("snippet") or "")[:300]
        compact.append(f"- {r.get('title') or 'Untitled'} | {u} | {snippet}")

    if not compact:
        return {"evidence": []}

    extractor = llm.with_structured_output(EvidencePack)
    pack = extractor.invoke([
        SystemMessage(content=RESEARCH_SYSTEM),
        HumanMessage(
            content=(
                f"As-of date: {state['as_of']}\n"
                f"Recency days: {state['recency_days']}\n\n"
                f"Raw results (deduped):\n" + "\n".join(compact)
            )
        )
    ])
    
    # In the time of research if it give duplicate link then it will only keep unique links
    # we do dict and then pass all links as key and it's name as value,
    # so where there are duplicate key is there, it will remove.
    dedup = {}
    for e in pack.evidence:
        if e.url:
            dedup[e.url] = e
    evidence = list(dedup.values())
    
    # Recency filtering for open_book: drop items that are clearly older than
    # the cutoff, but KEEP items with an unknown date — dropping them leaves
    # the writers with no grounding at all, which invites hallucination.
    if state.get("mode") == "open_book":
        as_of = date.fromisoformat(state["as_of"])
        cutoff = as_of - timedelta(days=int(state["recency_days"]))
        kept = []
        for e in evidence:
            d = _iso_to_date(e.published_at)
            if d is None or d >= cutoff:
                kept.append(e)
        evidence = kept

    return {"evidence": evidence}