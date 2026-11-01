from utils.prompts import create_farming_prompt
from backend.llm import generate_response

prompt = create_farming_prompt(
    crop="Wheat",
    location="Katihar, Bihar",
    weather={
        "temperature": "25.7°C",
        "humidity": "89%",
        "rainfall": "0 mm"
    },
    question="Should I irrigate my wheat field?",
    language="Hindi"
)

response = generate_response(prompt)

print(response)