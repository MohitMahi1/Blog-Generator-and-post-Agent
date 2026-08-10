import re
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm import llm
from app.core.config import settings
from app.schemas.models import GlobalImagePlan
from app.graph.state import State

"""
    Here we do merge all the content, or all the section which are coming
    by worker node.
    And Here we do import required images when images need to show in our
    blog.
"""

def _sanitize_links(md: str, allowed_urls: set) -> str:
    """
    Drop markdown links that are malformed (title-as-URL, spaces) or point at
    a URL that was never in the evidence set. Keeps only links to allowed
    sources, guaranteeing every citation resolves to real research.
    """
    def repl(m):
        text, url = m.group(1), m.group(2).rstrip(")")
        if re.match(r"^https?://\S+$", url) and url in allowed_urls:
            return m.group(0)
        return text

    # Negative lookbehind so ![alt](...) image syntax is never touched.
    return re.sub(r"(?<!\!)\[([^\]]+)\]\(([^)]*)\)", repl, md)


# Merge content
def merge_content(state: State) -> dict:
    plan = state["plan"]
    
    # If there is no plan
    if plan is None:
        raise ValueError("merge_content called without plan.")
    
    # The worker may finish in different order, so we have to sort them.
    # Dedupe by task id first: the parent can echo `sections` back into this
    # subgraph's input, which would otherwise duplicate every section.
    sections_by_id = {}
    for task_id, md in state["sections"]:
        sections_by_id[task_id] = md
    allowed_urls = {e.url for e in state.get("evidence", [])}
    ordered_sections = [_sanitize_links(sections_by_id[i], allowed_urls) for i in sorted(sections_by_id)]
    
    body = "\n\n".join(ordered_sections).strip()
    merged_md = f"# {plan.blog_title}\n\n{body}\n"
    return {"merged_md": merged_md}

# Decide all the details of image in prompt.
DECIDE_IMAGES_SYSTEM = """You are an expert technical editor.
Decide if an image/diagram is needed for THIS blog.

Rules:
- Max 1 image total.
- The image must materially improve understanding (diagram/flow/header visual).
- Insert placeholder exactly: [[IMAGE_1]].
- If no image needed: md_with_placeholders must equal input and images=[].
- Prefer technical diagrams with short labels.
Return strictly GlobalImagePlan.
"""

# decide which images take 
def decide_images(state : State) -> dict:
    planner = llm.with_structured_output(GlobalImagePlan)
    merged_md = state["merged_md"]
    plan = state["plan"]
    
    assert plan is not None
    
    image_plan = planner.invoke(
        [
            SystemMessage(content=DECIDE_IMAGES_SYSTEM),
            HumanMessage(
                content=(
                    f"Blog kind: {plan.blog_kind}\n"
                    f"Topic: {state['topic']}\n\n"
                    "Insert placeholders + propose image prompts.\n\n"
                    f"{merged_md}"
                )
            ),
        ]
    )
    
    # Restrict to maximum 1 image as requested, normalizing size/quality so a
    # stray value from the LLM can never crash the pipeline.
    valid_sizes = {"1024x1024", "1024x1536", "1536x1024"}
    valid_quality = {"low", "medium", "high"}
    selected_images = []
    for img in image_plan.images[:1]:
        spec = img.model_dump()
        spec["size"] = spec.get("size") if spec.get("size") in valid_sizes else "1024x1024"
        spec["quality"] = spec.get("quality") if spec.get("quality") in valid_quality else "medium"
        selected_images.append(spec)
    
    return {
        "md_with_placeholders": image_plan.md_with_placeholders,
        "image_specs": selected_images,
    }
    
    
# Image Generation via google gemini
def _gemini_generate_image_bytes(prompt: str) -> bytes:
    """
    Generate image using Gemini/Imagen and return raw bytes.
    """
    from google import genai
    from google.genai import types

    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set in environment variables.")

    client = genai.Client(api_key=api_key)

    models_to_try = [
        "imagen-3.0-generate-002",
        "gemini-2.5-flash",
        "gemini-3.1-flash-lite-image",
    ]

    last_error = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                ),
            )

            # Method 1: response.parts
            if hasattr(response, "parts") and response.parts:
                for part in response.parts:
                    if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                        return part.inline_data.data
                    if hasattr(part, "as_image"):
                        try:
                            img = part.as_image()
                            from io import BytesIO
                            buf = BytesIO()
                            img.save(buf, format="PNG")
                            return buf.getvalue()
                        except Exception:
                            pass

            # Method 2: candidates[0].content.parts
            if hasattr(response, "candidates") and response.candidates:
                try:
                    parts = response.candidates[0].content.parts
                    for part in parts:
                        if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                            return part.inline_data.data
                except Exception:
                    pass
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(
        f"No image data found from models {models_to_try}. Last error: {last_error}"
    )


# turns a blog title into a filesystem-safe filename
def _safe_slug(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9 _-]+", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "blog"

# orchestrates image generation + final write
def generate_and_place_images(state: State) -> dict:
    plan = state["plan"]
    assert plan is not None

    md = state.get("md_with_placeholders") or state["merged_md"]
    image_specs = state.get("image_specs", []) or []

    if not image_specs:
        return {"final": md}

    images_dir = Path("images")
    images_dir.mkdir(exist_ok=True)

    for spec in image_specs:
        placeholder = spec["placeholder"]
        filename = spec["filename"]
        out_path = images_dir / filename

        if not out_path.exists():
            try:
                img_bytes = _gemini_generate_image_bytes(spec["prompt"])
                out_path.write_bytes(img_bytes)
            except Exception as e:
                prompt_block = (
                    f"> **[IMAGE GENERATION FAILED]** {spec.get('caption','')}\n>\n"
                    f"> **Alt:** {spec.get('alt','')}\n>\n"
                    f"> **Prompt:** {spec.get('prompt','')}\n>\n"
                    f"> **Error:** {e}\n"
                )
                md = md.replace(placeholder, prompt_block)
                continue

        img_md = f"![{spec['alt']}](images/{filename})\n*{spec['caption']}*"
        md = md.replace(placeholder, img_md)

    return {"final": md}