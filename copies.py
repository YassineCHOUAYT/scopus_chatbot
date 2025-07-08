#scopus_fetch.py copy 
# scopus_fetch.py

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SCOPUS_API_KEY")
HEADERS = {"X-ELS-APIKey": API_KEY}
QUERY = "machine learning"
COUNT = 25
OUTPUT_FILE = "data/scopus_articles.json"

def fetch_scopus_articles(query, count=25):
    url = "https://api.elsevier.com/content/search/scopus"
    params = {"query": query, "count": count, "sort": "relevancy"}
    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code != 200:
        print("❌ Erreur API :", response.status_code, response.text)
        return []

    data = response.json()
    entries = data.get("search-results", {}).get("entry", [])

    articles = []
    for entry in entries:
        articles.append({
            "id": entry.get("dc:identifier", "").replace("SCOPUS_ID:", ""),
            "title": entry.get("dc:title", ""),
            "abstract": entry.get("dc:description", ""),
            "authors": entry.get("dc:creator", ""),
            "published": entry.get("prism:coverDate", ""),
            "updated": None,
            "link": "",
            "primary_category": "",
            "category": "",
            "doi": entry.get("prism:doi", ""),
            "journal_ref": entry.get("prism:publicationName", "")
        })

    return articles

def save_articles_to_file(articles, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    articles = fetch_scopus_articles(QUERY, COUNT)
    if articles:
        save_articles_to_file(articles, OUTPUT_FILE)
        print(f"✅ {len(articles)} articles sauvegardés dans '{OUTPUT_FILE}'")
    else:
        print("Aucun article récupéré.")
