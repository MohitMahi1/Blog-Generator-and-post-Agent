import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pathlib import Path

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
print("API Key loaded:", "Yes" if api_key else "NO - KEY MISSING")

client = genai.Client(api_key=api_key)

prompt = "A simple technical diagram of a neural network, clean white background, labeled nodes"

print("Calling Gemini...")

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )
    print("Response received")

    # Try to extract image
    image_data = None

    if hasattr(response, "parts") and response.parts:
        for part in response.parts:
            if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                image_data = part.inline_data.data
                print("Found image in response.parts")
                break

    if not image_data and hasattr(response, "candidates"):
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                image_data = part.inline_data.data
                print("Found image in candidates")
                break

    if image_data:
        Path("test_output.png").write_bytes(image_data)
        print("✅ SUCCESS! Image saved as test_output.png")
    else:
        print("❌ No image data found in response")
        print("Full response:", response)

except Exception as e:
    print("❌ ERROR:")
    print(type(e).__name__, "→", e)