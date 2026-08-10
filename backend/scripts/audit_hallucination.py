"""
Hallucination & quality audit for the blog-writing graph.

Runs the full pipeline on a volatile (open_book-style) topic and saves
artifacts under backend/audit_output/ for manual review:

  - final.md         the generated blog
  - logs.txt         per-node logs
  - evidence.json    (title, url) pairs the research node actually found
  - plan.json        the outline the orchestrator produced

Also prints a citation cross-check: every link used in the final markdown
vs. the URLs that were actually provided as evidence. Links pointing at
URLs NOT in the evidence set are red flags (potential fabrication).

Image generation is skipped (swapped for a no-op) to keep audit costs low.

Usage:  python scripts/audit_hallucination.py ["custom topic"]
Env:    AUDIT_TOPIC overrides the topic; AUDIT_AS_OF overrides the date.
"""

import json
import os
import pathlib
import re
import sys

sys.path.insert(0, os.getcwd())  # ensure backend/ is importable

# --- Skip image generation for the audit (cost control) -------------------
import app.graph.nodes.reducer as reducer_mod  # noqa: E402


def _noop_images(state):
    return {"final": state.get("merged_md", "")}


reducer_mod.generate_and_place_images = _noop_images

# Import AFTER patching so the compiled graph picks up the no-op.
from app.graph.build import app_graph  # noqa: E402
from app.schemas.models import GenerateRequest  # noqa: E402
from app.services.blog_service import generate_blog  # noqa: E402


def main():
    topic = os.getenv("AUDIT_TOPIC") or (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Latest AI agent frameworks and MCP tooling news — week of August 3, 2026"
    )
    as_of = os.getenv("AUDIT_AS_OF", "2026-08-10")

    print(f"Topic : {topic}")
    print(f"As-of : {as_of}")
    print("Running pipeline (this calls Mistral + Tavily)…")

    resp = generate_blog(GenerateRequest(topic=topic, as_of=as_of))

    out_dir = pathlib.Path("audit_output")
    out_dir.mkdir(exist_ok=True)

    markdown = resp.final_markdown or ""
    (out_dir / "final.md").write_text(markdown, encoding="utf-8")
    (out_dir / "logs.txt").write_text("\n".join(resp.logs or []), encoding="utf-8")

    evidence = [(e.title, e.url, e.published_at) for e in (resp.evidence or [])]
    (out_dir / "evidence.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / "plan.json").write_text(
        json.dumps(resp.plan.model_dump() if resp.plan else None, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # ---- Citation cross-check -------------------------------------------
    evidence_urls = {e.url for e in (resp.evidence or [])}
    links = re.findall(r"\]\((https?://[^)\s]+)\)", markdown)
    cited_not_in_evidence = [u for u in links if u not in evidence_urls]

    unsupported_markers = markdown.count("Not found in provided sources")

    print("\n================ AUDIT SUMMARY ================")
    print(f"mode           : {resp.mode}")
    print(f"sections       : {resp.sections_count}")
    print(f"evidence items : {len(resp.evidence or [])}")
    print(f"total links    : {len(links)}")
    print(f"links NOT in evidence : {len(cited_not_in_evidence)}")
    for u in cited_not_in_evidence:
        print("   [WARN]", u[:140])
    print(f"'Not found in sources' markers : {unsupported_markers}")
    print(f"artifacts saved to: {out_dir.resolve()}")
    print("===============================================")


if __name__ == "__main__":
    main()
