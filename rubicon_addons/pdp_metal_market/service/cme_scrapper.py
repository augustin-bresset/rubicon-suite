import requests

import os
import requests
from dotenv import load_dotenv

# Load .env file at project root
load_dotenv()

API_KEY = os.getenv("API_KEY_METAL_MARKET")

BASE_URL = "https://api.metalpriceapi.com/v1/"


def get_metal_prices(date=None, test=True):
    """
    Get metal prices for:
    - today (if date=None)
    - or a specific date (YYYY-MM-DD)
    """

    if test:
        # 2025-11-23
        return {
            'gold': 4064.9216770891, 
            'silver': 49.9913197572, 
            'platinum': 1516.3825420698, 
            'palladium': 1381.9184538212}

    if not API_KEY:
        raise ValueError("Missing METALPRICE_API_KEY in .env")

    date = 'latest' if date is None else date

    # Endpoint changes depending on date
    endpoint = f"{BASE_URL}/{date}"
    
    url = (
        f"{endpoint}?api_key={API_KEY}"
        f"&base=USD"
        f"&currencies=XAU,XAG,XPT,XPD"
    )

    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()

    if not data.get("success", True):
        raise RuntimeError(f"API error: {data}")

    rates = data["rates"]

    return {
        "gold": rates["USDXAU"],
        "silver": rates["USDXAG"],
        "platinum": rates["USDXPT"],
        "palladium": rates["USDXPD"],
    }


if __name__ == "__main__":
    
    # print(get_metal_prices())
    ...
    # print(get_metal_prices("2024-01-01"))