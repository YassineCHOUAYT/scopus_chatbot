import mysql.connector
import json
from sentence_transformers import SentenceTransformer
import numpy as np

MODEL_NAME = 'all-MiniLM-L6-v2'

def fetch_abstracts():
    conn = mysql.connector.connect(
        host="localhost", user="root", password="", database="arxiv_db", charset='utf8mb4')
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, abstract FROM articles WHERE abstract IS NOT NULL")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def update_embedding(article_id, embedding):
    conn = mysql.connector.connect(
        host="localhost", user="root", password="", database="arxiv_db", charset='utf8mb4')
    cursor = conn.cursor()
    emb_json = json.dumps(embedding.tolist())
    update_q = "UPDATE articles SET embedding=%s WHERE id=%s"
    cursor.execute(update_q, (emb_json, article_id))
    conn.commit()
    cursor.close()
    conn.close()

def generate_and_store_embeddings():
    model = SentenceTransformer(MODEL_NAME)
    abstracts = fetch_abstracts()
    print(f"[embedding.py] {len(abstracts)} abstracts à vectoriser...")
    for article in abstracts:
        emb = model.encode(article['abstract'])
        update_embedding(article['id'], emb)
    print("[embedding.py] Terminé.")

if __name__ == "__main__":
    generate_and_store_embeddings()
