#utils/serpapi_competitor_search.py

import requests
from typing import List, Dict
from config.settings import SERPAPI_API_KEY


def fetch_competitors_from_serpapi(query: str, num_results: int = 10) -> List[Dict]:
    """
    Fetch a list of competitors from Google Search using SerpAPI.

    Args:
        query (str): The search query string (e.g., "Top IT companies in Berlin").
        num_results (int): Number of results to fetch.

    Returns:
        List[Dict]: A list of dictionaries with competitor_name, description, and link.
    """
    if not SERPAPI_API_KEY:
        raise EnvironmentError("SERPAPI_API_KEY not set in environment variables.")

    url = "https://serpapi.com/search"
    params = {
        "q": query,
        "engine": "google",
        "api_key": SERPAPI_API_KEY,
        "num": num_results
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    competitors = []
    for result in data.get("organic_results", []):
        competitors.append({
            "competitor_name": result.get("title", "Unknown"),
            "description": result.get("snippet", "No description available."),
            "link": result.get("link", "")
        })

    return competitors