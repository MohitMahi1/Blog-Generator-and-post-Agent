import os, re
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm import llm
from app.schemas.models import GlobalImagePlan
from app.graph.state import State

"""
    Here we do merge all the content, or all the section which are coming
    by worker node.
    And Here we do import required images when images need to show in our
    blog.
"""

# Merge content
def merge_content(state: State) -> dict:
    plan = state["plan"]
    
    # If there is no plan
    if plan is None:
        raise ValueError("merge_content called without plan.")
    
    # The worker may finish in different order, so we have to sort them
    ordered_sections = [
        md for _, md in sorted(
            state["sections"], key=lambda x: x[0]
        )
    ]
    
    body = "\n\n".join(ordered_sections).strip()
    merged_md = f"# {plan.blog_title}\n\n{body}\n"
    return {"merged_md": merged_md}

# Decide all the details of image in prompt.
DECIDE_IMAGES_SYSTEM = """You are an expert technical editor.
Decide if images/diagrams are needed for THIS blog.

Rules:
- Max 3 images total.
- Each image must materially improve understanding (diagram/flow/table-like visual).
- Insert placeholders exactly: [[IMAGE_1]], [[IMAGE_2]], [[IMAGE_3]].
- If no images needed: md_with_placeholders must equal input and images=[].
- Avoid decorative images; prefer technical diagrams with short labels.
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
    
    return {
        "md_with_placeholders": image_plan.md_with_placeholders,
        "image_specs": [img.model_dump() for img in image_plan.images],
    }
    
    
# Image Generation via google gemini
def _gemini_generate_image_bytes(prompt: str) -> bytes:
    """
    Generate image using Gemini (Nano Banana) and return raw bytes.
    """
    from google import genai
    from google.genai import types
    import os

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set in environment variables.")

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",          # stable name
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}")

    # ---------- Robust extraction ----------
    # Method 1: response.parts (newer SDK)
    if hasattr(response, "parts") and response.parts:
        for part in response.parts:
            if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                return part.inline_data.data
            # some versions have as_image()
            if hasattr(part, "as_image"):
                try:
                    img = part.as_image()
                    from io import BytesIO
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    return buf.getvalue()
                except Exception:
                    pass

    # Method 2: candidates[0].content.parts (older style)
    if hasattr(response, "candidates") and response.candidates:
        try:
            parts = response.candidates[0].content.parts
            for part in parts:
                if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                    return part.inline_data.data
        except Exception:
            pass

    # If we reach here → no image was returned
    raise RuntimeError(
        "No image data found in Gemini response. "
        "Possible reasons: safety filter, quota, or model returned only text."
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
        filename = f"{_safe_slug(plan.blog_title)}.md"
        Path(filename).write_text(md, encoding="utf-8")
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

    filename = f"{_safe_slug(plan.blog_title)}.md"
    Path(filename).write_text(md, encoding="utf-8")
    return {"final": md}