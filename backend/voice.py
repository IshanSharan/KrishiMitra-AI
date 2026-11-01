import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


def transcribe_farmer_audio(audio_bytes, mime_type="audio/wav", language="Hindi"):
    """Convert a farmer's recorded question into text using Gemini audio understanding."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env")

    client = genai.Client(api_key=api_key)
    prompt = (
        f"Listen to this farmer's audio and transcribe only the spoken question. "
        f"The language may be {language}, English, or a mixture. "
        "Preserve the original language. Do not answer the question. "
        "If speech is unclear, return a short note saying it was unclear."
    )
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            prompt
        ]
    )
    text = (response.text or "").strip()
    if not text:
        raise ValueError("Could not transcribe the audio. Please try recording again.")
    return text
