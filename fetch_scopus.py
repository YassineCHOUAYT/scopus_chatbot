import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import time
from insert_mysql import insert_articles  

ARXIV_API_URL = "http://export.arxiv.org/api/query"
BATCH_SIZE = 1000
REQUEST_INTERVAL = 4  # secondes

def extract_entry_data(entry, ns):
    try:
        title = entry.find('atom:title', ns).text.strip()
        summary = entry.find('atom:summary', ns).text.strip()
        published = entry.find('atom:published', ns).text
        updated = entry.find('atom:updated', ns).text
        link = entry.find('atom:id', ns).text
        arxiv_id = link.split('/')[-1]

        authors = [author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)]
        categories = [cat.attrib['term'] for cat in entry.findall('atom:category', ns)]

        primary_category = ""
        primary_elem = entry.find('atom:primary_category', ns)
        if primary_elem is not None:
            primary_category = primary_elem.attrib.get('term', '')

        doi = None
        doi_elem = entry.find('.//atom:link[@title="doi"]', ns)
        if doi_elem is not None and 'doi.org' in doi_elem.attrib.get('href', ''):
            doi = doi_elem.attrib['href'].split('doi.org/')[-1]

        journal_ref = entry.find('atom:journal_ref', ns)
        journal_ref = journal_ref.text.strip() if journal_ref is not None else None

        return {
            "id": arxiv_id,
            "title": title,
            "authors": ', '.join(authors),
            "published": published,
            "updated": updated,
            "link": link,
            "abstract": summary,
            "primary_category": primary_category,
            "category": ', '.join(categories),
            "doi": doi,
            "journal_ref": journal_ref
        }
    except Exception as e:
        print(f"Erreur lors de l'extraction d'une entrée: {e}")
        return None

def fetch_arxiv_articles(start_date, end_date):
    start_str = start_date.strftime("%Y%m%d0000")
    end_str = end_date.strftime("%Y%m%d2359")
    query = f"submittedDate:[{start_str} TO {end_str}]"
    print(f"🔎 Période {start_str} ➡ {end_str}")

    total_inserted = 0
    start = 0

    while True:
        params = {
            "search_query": query,
            "start": start,
            "max_results": BATCH_SIZE,
            "sortBy": "submittedDate"
        }

        try:
            response = requests.get(ARXIV_API_URL, params=params, timeout=45)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            entries = root.findall('atom:entry', ns)

            if not entries:
                break

            articles = []
            for entry in entries:
                article = extract_entry_data(entry, ns)
                if article:
                    articles.append(article)

            if articles:
                inserted_count = insert_articles(articles)
                print(f"✅ {inserted_count} articles insérés pour {start_str}")
                total_inserted += inserted_count

            start += BATCH_SIZE
            time.sleep(REQUEST_INTERVAL)

        except Exception as e:
            print(f"❌ Erreur : {e}")
            break

    print(f"🎯 Total inséré pour {start_str}: {total_inserted}")
    return total_inserted

# Exemple d'utilisation si lancé directement
if __name__ == "__main__":
    from datetime import datetime
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2023, 1, 4)
    fetch_arxiv_articles(start_date, end_date)
