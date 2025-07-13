from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json

class SemanticIndexer:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.embeddings = None
        self.article_ids = []
        self.articles = []

    def load_articles(self, json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.articles = data['articles']
        self.article_ids = [a['arxiv_id'] for a in self.articles]
        abstracts = [a['abstract'] for a in self.articles]
        return abstracts

    def create_index(self, abstracts):
        print("Vectorisation des résumés...")
        self.embeddings = self.model.encode(abstracts, show_progress_bar=True)

        dim = self.embeddings[0].shape[0]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(np.array(self.embeddings))

        print(f"✅ Index FAISS créé avec {self.index.ntotal} vecteurs.")

    def save_index(self, path='arxiv_index.faiss'):
        faiss.write_index(self.index, path)
        print(f"Index sauvegardé dans {path}")

    def save_metadata(self, path='arxiv_metadata.json'):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.articles, f, indent=2, ensure_ascii=False)
        print(f"Métadonnées sauvegardées dans {path}")

    def index_from_json(self, json_path):
        abstracts = self.load_articles(json_path)
        self.create_index(abstracts)
        self.save_index()
        self.save_metadata()

    def load_index(self, index_path='arxiv_index.faiss', metadata_path='arxiv_metadata.json'):
        print("Chargement de l'index FAISS et des métadonnées...")
        self.index = faiss.read_index(index_path)

        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.articles = json.load(f)
        self.article_ids = [a['arxiv_id'] for a in self.articles]

        print(f"Index chargé avec {self.index.ntotal} vecteurs.")

# La fonction de recherche sémantique reste en dehors de la classe
def semantic_search(query, index_path='arxiv_index.faiss', metadata_path='arxiv_metadata.json', model_name='all-MiniLM-L6-v2', top_k=5):
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
    import json

    print("Chargement du modèle et de l’index...")
    model = SentenceTransformer(model_name)
    index = faiss.read_index(index_path)

    with open(metadata_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    query_embedding = model.encode([query])
    D, I = index.search(np.array(query_embedding), top_k)

    print("\n🔍 Résultats de la recherche sémantique :")
    for rank, idx in enumerate(I[0]):
        article = articles[idx]
        print(f"{rank + 1}. {article['title']}")
        print(f"Résumé : {article['abstract'][:300]}...\n")
