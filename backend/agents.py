from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from backend.weather import get_weather
from backend.rag_chain import ask_krishimitra


class KrishiState(TypedDict):
    city: str
    crop: str
    question: str
    language: str
    soil_metrics: dict
    sowing_date: Optional[str]
    weather: dict
    location: str
    response: str


def weather_node(state: KrishiState):
    print("\\nFetching weather information...")
    weather = get_weather(state["city"])
    location = f'{weather["location"]}, {weather["state"]}'
    return {"weather": weather, "location": location}


def advisory_node(state: KrishiState):
    print("\\nGenerating agricultural advisory...")
    response = ask_krishimitra(
        crop=state["crop"],
        location=state["location"],
        weather=state["weather"],
        question=state["question"],
        language=state["language"],
        soil_metrics=state.get("soil_metrics", {}),
        sowing_date=state.get("sowing_date")
    )
    return {"response": response}


graph = StateGraph(KrishiState)
graph.add_node("weather", weather_node)
graph.add_node("advisory", advisory_node)
graph.set_entry_point("weather")
graph.add_edge("weather", "advisory")
graph.add_edge("advisory", END)
krishi_app = graph.compile()


def run_krishimitra(
    city, crop, question, language="Hindi",
    soil_metrics=None, sowing_date=None
):
    initial_state = {
        "city": city,
        "crop": crop,
        "question": question,
        "language": language,
        "soil_metrics": soil_metrics or {},
        "sowing_date": sowing_date,
        "weather": {},
        "location": "",
        "response": ""
    }
    result = krishi_app.invoke(initial_state)
    return {
        "weather": result["weather"],
        "location": result["location"],
        "response": result["response"]
    }
