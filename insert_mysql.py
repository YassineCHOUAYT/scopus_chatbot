from config import get_connection

def insert_articles(articles):
    conn = get_connection()
    cursor = conn.cursor()

    insert_query = """
        INSERT IGNORE INTO articles
        (id, title, authors, published, updated, link, abstract, primary_category, category, doi, journal_ref)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = []
    for art in articles:
        values.append((
            art['id'],
            art['title'],
            art['authors'],
            art['published'],
            art['updated'],
            art['link'],
            art['abstract'],
            art['primary_category'],
            art['category'],
            art['doi'],
            art['journal_ref']
        ))

    try:
        cursor.executemany(insert_query, values)
        conn.commit()
        inserted = cursor.rowcount
    except Exception as e:
        print(f"❌ Erreur insertion article {articles[0]['id'] if articles else 'N/A'}: {e}")
        inserted = 0
    finally:
        cursor.close()
        conn.close()

    return inserted
