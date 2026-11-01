
from backend.rag_chain import ask_krishimitra
from backend.weather import get_weather


print("\n===== KRISHIMITRA RAG TEST =====")

# Farmer inputs
city = input("\nEnter city: ").strip()

crop = input("Enter crop: ").strip()

question = input("Enter farming question: ").strip()

language = input("Enter language (Hindi/English): ").strip()

if not language:
    language = "Hindi"

try:

    # Fetch weather
    print("\nFetching weather information...")

    weather = get_weather(city)

    location = f"{weather['location']}, {weather['state']}"

    print("\nDetected location:", location)

    # Generate RAG response
    response = ask_krishimitra(
        crop=crop,
        location=location,
        weather=weather,
        question=question,
        language=language
    )

    print("\n===== KRISHIMITRA AI RESPONSE =====\n")

    print(response)

    print("\n===== TEST COMPLETED =====")

except Exception as e:

    print("\nERROR:", e)
