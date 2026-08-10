from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm import llm
from app.schemas.models import Task, Plan, EvidenceItem

# Working prompt when all section are divide and fanout assign the work to every worker
WORKER_SYSTEM = """You are a senior technical writer and developer advocate.
Write ONE section of a technical blog post in Markdown.

Constraints:
- Cover ALL bullets in order.
- Target words ±15%.
- Output only section markdown starting with "## <Section Title>".

Scope guard:
- If blog_kind=="news_roundup", do NOT drift into tutorials.
  Focus on events + implications.

Grounding:
- NEVER invent specifics: version numbers, percentages, statistics, dates, prices, funding amounts, or vendor quotes. If a specific number or detail is not in the provided sources, write "Not found in provided sources."
- If mode=="open_book": do not introduce any specific event/company/model/policy claim unless supported by provided Evidence URLs.
  For each supported claim, attach a Markdown link ([Source](URL)).
  If unsupported, write "Not found in provided sources."
- If requires_citations==true: cite Evidence URLs for external claims.
- Do NOT link to any URL that is not in the Allowed sources list.
- Link URLs must be EXACT http(s) URLs copied from the Allowed sources list — never a title or description as a URL.

Code:
- If requires_code==true, include at least one minimal snippet.
"""

# worker node
def worker_node(payload : dict) -> dict:
    task = Task(**payload["task"])
    plan = Plan(**payload["plan"])
    mode = payload.get("mode", "closed_book")
    
    evidence = [EvidenceItem(**e) for e in payload.get("evidence", [])]
    
    bullets_text = "\n- " + "\n- ".join(task.bullets)

    # Only include evidence when this section can actually cite it —
    # saves tokens on every other section.
    needs_citations = task.requires_citations or task.requires_research or mode in ("open_book", "hybrid")
    if needs_citations and evidence:
        evidence_text = "\n".join(
            f"- {e.title} | {e.url} | {e.published_at or 'date:unknown'}"
            for e in evidence[:8]
        )
    else:
        evidence_text = "(none — this section must not cite external sources)"

    constraints_text = "; ".join(plan.constraints) if plan.constraints else "(none)"

    section_md = llm.invoke(
        [
            SystemMessage(content=WORKER_SYSTEM),
            HumanMessage(
                content=(
                    f"Blog title: {plan.blog_title}\n"
                    f"Audience: {plan.audience}\n"
                    f"Tone: {plan.tone}\n"
                    f"Blog kind: {plan.blog_kind}\n"
                    f"Constraints: {constraints_text}\n"
                    f"Topic: {payload['topic']}\n"
                    f"Mode: {mode}\n\n"
                    f"## Section to write\n"
                    f"Title: {task.title}\n"
                    f"Goal: {task.goal}\n"
                    f"Target words: {task.target_words}\n"
                    f"Tags: {task.tags}\n"
                    f"requires_citations: {needs_citations}\n"
                    f"requires_code: {task.requires_code}\n"
                    f"Bullets:{bullets_text}\n\n"
                    f"Allowed sources (cite ONLY these URLs):\n{evidence_text}\n"
                )
            ),
        ]
    ).content.strip()

    return {"sections": [(task.id, section_md)]}