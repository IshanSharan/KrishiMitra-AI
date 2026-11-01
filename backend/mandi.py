
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DATA_GOV_API_KEY")

RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"

API_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"


def get_mandi_prices(state, district, commodity, market=None):

    if not API_KEY:
        raise ValueError("API key not found in .env")

    params = {
        "api-key": API_KEY,
        "format": "json",
        "offset": 0,
        "limit": 10,
        "filters[state.keyword]": state,
        "filters[district]": district,
        "filters[commodity]": commodity
    }

    if market:
        params["filters[market]"] = market

   
    response = requests.get(
    API_URL,
    params=params,
    timeout=(10, 120)
)
    response.raise_for_status()

    data = response.json()

    return data.get("records", [])


if __name__ == "__main__":

    print("===== KRISHIMITRA MANDI PRICE CHECKER =====")

    # User Inputs
    state = input("Enter State (e.g. Bihar): ").strip()
    district = input("Enter District (e.g. Katihar): ").strip()
    commodity = input("Enter Crop (e.g. Wheat, Rice, Maize): ").strip()
    market = input("Enter Market (optional, press Enter to skip): ").strip()

    try:

        records = get_mandi_prices(
            state=state,
            district=district,
            commodity=commodity,
            market=market if market else None
        )

        if not records:
            print("\nNo records found for these inputs.")

        for item in records:

            print("\n----------------------------")
            print("State:", item.get("state"))
            print("District:", item.get("district"))
            print("Market:", item.get("market"))
            print("Commodity:", item.get("commodity"))
            print("Variety:", item.get("variety"))
            print("Min Price:", item.get("min_price"))
            print("Max Price:", item.get("max_price"))
            print("Modal Price:", item.get("modal_price"))
            print("Arrival Date:", item.get("arrival_date"))

    except requests.RequestException as e:
        print("API request error:", e)

    except ValueError as e:
        print("Error:", e)
