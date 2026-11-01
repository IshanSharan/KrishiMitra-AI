
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    google_api_key=API_KEY
)


def generate_response(prompt):
    response = llm.invoke(prompt)

    if isinstance(response.content, str):
        return response.content

    return "\n".join(
        item["text"]
        for item in response.content
        if item["type"] == "text"
    )