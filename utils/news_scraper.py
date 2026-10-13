#utils/news_scraper.py

import logging

logger = logging.getLogger(__name__)


def fetch_top_news_snippets(query: str, num_results: int = 5) -> list:
    """
    Fetch top news snippets from SerpAPI for a given query.
    Returns empty list on any failure (missing API key, network error, etc.)
    so the pipeline never crashes.
    """
    try:
        from config.settings import SERPAPI_API_KEY
        
        if not SERPAPI_API_KEY:
            logger.warning("SERPAPI_API_KEY is not configured. Skipping news fetch.")
            return []

        from serpapi.google_search import GoogleSearch
        
        params = {
            "q": f"{query} industry news",
            "tbm": "nws",
            "api_key": SERPAPI_API_KEY
        }
        search = GoogleSearch(params)
        results = search.get_dict()

        snippets = []
        for news in results.get("news_results", [])[:num_results]:
            title = news.get("title")
            snippet = news.get("snippet", "")
            if title:
                snippets.append(f"{title} - {snippet}")
        
        logger.info(f"Fetched {len(snippets)} news snippets for query: {query}")
        return snippets

    except ImportError:
        logger.warning("serpapi package not installed. Skipping news fetch.")
        return []
    except Exception as e:
        logger.error(f"Error fetching news snippets for '{query}': {e}")
        return []