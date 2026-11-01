
from backend.weather import get_weather
from backend.llm import generate_response
from utils.prompts import create_farming_prompt

city = input("Enter your city: ")
crop = input("Enter your crop: ")
question = input("Ask your farming question: ")

# Step 1: Fetch real weather data
weather = get_weather(city)

# Step 2: Create prompt
prompt = create_farming_prompt(
    crop=crop,
    location=f"{weather['location']}, {weather['state']}",
    weather=weather,
    question=question,
    language="Hindi"
)

# Step 3: Generate AI response
response = generate_response(prompt)

print("\n===== KRISHIMITRA AI =====\n")
print(response)
