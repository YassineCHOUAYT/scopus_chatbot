# scopus_fetch.py

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SCOPUS_API_KEY")
HEADERS = {
    "X-ELS-APIKey": API_KEY,
    "Accept": "application/json"
}
QUERY = "machine learning"
COUNT = 5
OUTPUT_FILE = "data/scopus_articles.json"

def get_full_metadata(scopus_id):
    url = f"https://api.elsevier.com/content/abstract/scopus_id/{scopus_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"❌ Erreur récupération Scopus ID {scopus_id}: {response.status_code}")
        return None

def extract_abstract(metadata, scopus_id):
    abstract = ""
    try:
        # First try: abstracts-retrieval-response -> item -> bibrecord -> abstracts -> abstract
        abstract_data = (
            metadata.get("abstracts-retrieval-response", {})
                    .get("item", {})
                    .get("bibrecord", {})
                    .get("abstracts", {})
                    .get("abstract", {})
        )
        para = abstract_data.get("para", "")
        if isinstance(para, list):
            abstract = " ".join(para)
        elif isinstance(para, str):
            abstract = para
            
        print(f"📝 Abstract via item pour {scopus_id}: {len(abstract)} caractères")
    except Exception as e:
        print(f"⚠️ Problème extraction abstract via item pour {scopus_id}: {e}")

    # Fallback 1: via core
    if not abstract:
        try:
            core_data = metadata.get("abstracts-retrieval-response", {}).get("core", {})
            abstract = core_data.get("dc:description", "")
            print(f"📝 Abstract via core pour {scopus_id}: {len(abstract)} caractères")
        except Exception as e:
            print(f"⚠️ Problème fallback core pour {scopus_id}: {e}")

    # Fallback 2: via coredata
    if not abstract:
        try:
            coredata = metadata.get("abstracts-retrieval-response", {}).get("coredata", {})
            abstract = coredata.get("dc:description", "")
            print(f"📝 Abstract via coredata pour {scopus_id}: {len(abstract)} caractères")
        except Exception as e:
            print(f"⚠️ Problème fallback coredata pour {scopus_id}: {e}")

    # Fallback 3: search in item directly
    if not abstract:
        try:
            item_data = metadata.get("abstracts-retrieval-response", {}).get("item", {})
            abstract = item_data.get("dc:description", "")
            print(f"📝 Abstract via item direct pour {scopus_id}: {len(abstract)} caractères")
        except Exception as e:
            print(f"⚠️ Problème fallback item direct pour {scopus_id}: {e}")

    return abstract

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
        scopus_id = entry.get("dc:identifier", "").replace("SCOPUS_ID:", "")
        print(f"🔍 Traitement de l'article {scopus_id}...")
        
        metadata = get_full_metadata(scopus_id)

        abstract = ""
        category = ""
        primary_category = ""
        link = ""

        if metadata:
            abstract = extract_abstract(metadata, scopus_id)

            # Extraction des catégories
            try:
                subject_areas = (
                    metadata.get("abstracts-retrieval-response", {})
                            .get("subject-areas", {})
                            .get("subject-area", [])
                )
                if isinstance(subject_areas, list):
                    category = ", ".join(
                        [s.get("@abbrev", "") for s in subject_areas if "@abbrev" in s]
                    )
                elif isinstance(subject_areas, dict):
                    category = subject_areas.get("@abbrev", "")
            except Exception as e:
                print(f"⚠️ Problème extraction subject-areas pour {scopus_id}: {e}")

            # Extraction du lien
            try:
                links = metadata.get("abstracts-retrieval-response", {}).get("coredata", {}).get("link", [])
                if isinstance(links, list):
                    for link_item in links:
                        if link_item.get("@rel") == "scopus":
                            link = link_item.get("@href", "")
                            break
            except Exception as e:
                print(f"⚠️ Problème extraction link pour {scopus_id}: {e}")

        # Use title as fallback if abstract is empty
        title = entry.get("dc:title", "")
        content_for_embedding = abstract if abstract else title
        
        articles.append({
            "id": scopus_id,
            "title": title,
            "abstract": abstract,
            "authors": entry.get("dc:creator", ""),
            "published": entry.get("prism:coverDate", ""),
            "updated": None,
            "link": link,
            "primary_category": primary_category,
            "category": category,
            "doi": entry.get("prism:doi", ""),
            "journal_ref": entry.get("prism:publicationName", ""),
            "content_for_embedding": content_for_embedding  # Add this field
        })

        print(f"✅ Article ajouté : {title[:60]}...")
        print(f"   Abstract: {len(abstract)} caractères")
        print(f"   Content for embedding: {len(content_for_embedding)} caractères")

    return articles

def save_articles_to_file(articles, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    print("📡 Récupération des articles depuis Scopus...")
    articles = fetch_scopus_articles(QUERY, COUNT)
    if articles:
        save_articles_to_file(articles, OUTPUT_FILE)
        print(f"✅ {len(articles)} articles enrichis et sauvegardés dans '{OUTPUT_FILE}'")
    else:
        print("❌ Aucun article récupéré.")