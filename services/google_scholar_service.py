import requests
import re
from config import SERPAPI_KEY

def extract_scholar_id(url: str) -> str:
    """Extracts the Google Scholar user ID from a given URL."""
    if not url:
        return ""
    match = re.search(r"user=([^&]+)", url)
    return match.group(1) if match else ""

def fetch_scholar_publications(scholar_link: str) -> tuple[bool, str | list[dict]]:
    """
    Fetches publications from Google Scholar Author API via SerpApi.
    Returns (success_boolean, data_or_error_message).
    """
    if not SERPAPI_KEY:
        return False, "SerpApi Key is not configured in .env."

    author_id = extract_scholar_id(scholar_link)
    if not author_id:
        return False, "Invalid Google Scholar Link. Could not find 'user=' parameter."

    params = {
        "engine": "google_scholar_author",
        "author_id": author_id,
        "api_key": SERPAPI_KEY,
        "num": 100 # Fetch up to 100 articles
    }
    
    try:
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            return False, f"SerpApi Error: {data['error']}"
            
        articles = data.get("articles", [])
        
        # Structure the articles for our app
        structured_articles = []
        for a in articles:
            year = a.get("year", "")
            try:
                year = int(year) if year else None
            except ValueError:
                year = None
                
            structured_articles.append({
                "title": a.get("title", ""),
                "authors": a.get("authors", ""),
                "journal_or_patent_office": a.get("publication", ""),
                "year": year,
                "cited_by": a.get("cited_by", {}).get("value", 0),
                "link": a.get("link", "")
            })
            
        return True, structured_articles

    except requests.exceptions.RequestException as e:
        return False, f"Network error connecting to SerpApi: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"
