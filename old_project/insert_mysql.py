# insert_mysql.py

import json
from config import get_connection

INPUT_FILE = "data/scopus_articles.json"

def insert_articles_to_db(articles):
    conn = get_connection()
    cursor = conn.cursor()

    for article in articles:
        try:
            cursor.execute("""
                INSERT INTO articles (
                    id, title, authors, published, updated, link, abstract,
                    primary_category, category, doi, journal_ref
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE title=VALUES(title);
            """, (
                article["id"],
                article["title"],
                article["authors"],
                article["published"] or None,
                article["updated"],
                article["link"],
                article["abstract"],
                article["primary_category"],
                article["category"],
                article["doi"],
                article["journal_ref"]
            ))
        except Exception as e:
            print(f"⚠️ Erreur lors de l’insertion de l’article {article['id']}: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ {len(articles)} articles insérés dans la base de données.")

if __name__ == "__main__":
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            articles = json.load(f)
        insert_articles_to_db(articles)
    except FileNotFoundError:
        print(f"❌ Fichier '{INPUT_FILE}' introuvable. Lance d'abord `scopus_fetch.py`.")
