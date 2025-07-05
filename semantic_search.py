import mysql.connector
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_NAME = 'all-MiniLM-L6-v2'

def fetch_articles_with_embeddings():
    conn = mysql.connector.connect(
        host="localhost", user="root", password="", database="arxiv_db", charset='utf8mb4')
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, title, abstract, embedding FROM articles WHERE embedding IS NOT NULL")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def semantic_search(query, top_k=5):
    model = SentenceTransformer(MODEL_NAME)
    q_vec = model.encode(query).reshape(1, -1)

    articles = fetch_articles_with_embeddings()
    embeddings = []
    ids = []
    for art in articles:
        emb = np.array(json.loads(art['embedding']))
        embeddings.append(emb)
        ids.append(art)

    embeddings = np.array(embeddings)
    similarities = cosine_similarity(q_vec, embeddings)[0]
    
    top_indices = similarities.argsort()[-top_k:][::-1]
    results = []
    for idx in top_indices:
        art = ids[idx]
        results.append({
            "id": art['id'],
            "title": art['title'],
            "abstract": art['abstract'],
            "score": similarities[idx]
        })
    return results

if __name__ == "__main__":
    query = input("Tape ta question scientifique : ")
    results = semantic_search(query)
    for i, res in enumerate(results, 1):
        print(f"\n{i}. {res['title']} (score: {res['score']:.3f})\n{res['abstract'][:300]}...\n")
