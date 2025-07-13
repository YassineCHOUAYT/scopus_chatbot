import faiss
import json
import numpy as np
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer

class ScopusChatbot:
    def __init__(self, index_path="arxiv_index.faiss", metadata_path="arxiv_metadata.json"):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.read_index(index_path)
        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    def process_query(self, query):
        query = query.lower()

        if "articles récents" in query:
            return self.get_recent_articles()

        if "travaux de" in query:
            name = query.split("travaux de")[-1].strip()
            return self.get_articles_by_author(name)

        if "statistiques" in query or "nombre d'articles" in query:
            return self.get_stats()

        return self.semantic_search(query)

    def semantic_search(self, query):
        q_emb = self.model.encode([query])
        _, I = self.index.search(np.array(q_emb).astype("float32"), 3)
        return [self.metadata[i] for i in I[0]]

    def get_articles_by_author(self, name):
         name = name.lower()
         result = []
         for art in self.metadata:
            authors = art.get("authors", [])
            for author in authors:
                 author_name = author.get("name", "").lower()
                 if name in author_name:
                     result.append(art)
                     break
         return result


    def get_recent_articles(self, days=30):
        cutoff = datetime.now() - timedelta(days=days)
        return [
            a for a in self.metadata
            if "published_date" in a and datetime.strptime(a["published_date"], "%Y-%m-%d") >= cutoff
        ]

    def get_stats(self):
        # Compter les auteurs uniques (par leur nom si possible)
        author_names = set()
        for art in self.metadata:
            for a in art.get("authors", []):
                if isinstance(a, dict) and "name" in a:
                    author_names.add(a["name"])
        return {
            "total_articles": len(self.metadata),
            "authors_count": len(author_names)
        }
