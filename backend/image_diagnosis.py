"""Image-assisted crop symptom triage. It must not claim a definitive diagnosis."""
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


def analyze_crop_image(image_bytes, mime_type, crop, location, language="Hindi", question=""):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env")
    client = genai.Client(api_key=api_key)
    prompt = f"""
You are KrishiMitra, an agricultural image-triage assistant.
Analyze the uploaded crop/leaf image for visible symptoms. Do not claim certainty.
Crop: {crop}
Location: {location}
Preferred language: {language}
Farmer's note: {question or 'No additional note'}

Respond in {language}, briefly:
1. Describe only visible symptoms.
2. Give up to 2-3 possible causes, clearly label them as possibilities, not a confirmed diagnosis.
3. Ask for missing details that materially affect diagnosis (crop age/stage, spread pattern,
   when it started, recent rain/irrigation, pesticide/fertilizer use).
4. Suggest safe immediate checks. Do not prescribe pesticide or fertilizer doses.
5. Recommend a local KVK/agriculture officer or lab confirmation before chemical treatment.
If image is unclear or not a crop image, say so and ask for a clearer photo.
"""
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime_type), prompt]
    )
    result = (response.text or "").strip()
    if not result:
        raise ValueError("Image analysis returned an empty response.")
    return result
