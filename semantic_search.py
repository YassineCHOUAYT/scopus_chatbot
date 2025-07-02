import pandas as pd
import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer
import sqlite3
from config import DATABASE_PATH, MODEL_NAME, VECTOR_INDEX_PATH

class SemanticSearch:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        self.index = None
        self.article_data = None
        self.db_path = DATABASE_PATH
    
    def create_embeddings(self):
        """Création des embeddings pour tous les articles"""
        print("Chargement des articles...")
        
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT id, scopus_id, title, abstract, publication_date, journal, keywords
            FROM articles
            WHERE abstract IS NOT NULL AND LENGTH(abstract) > 50
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print("Aucun article trouvé dans la base de données")
            return
        
        print(f"Création des embeddings pour {len(df)} articles...")
        
        # Préparation du texte pour embedding (titre + résumé)
        texts = df.apply(lambda row: f"{row['title']} {row['abstract']}", axis=1).tolist()
        
        # Génération des embeddings
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Création de l'index FAISS
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product pour similarité cosinus
        
        # Normalisation pour similarité cosinus
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype(np.float32))
        
        # Sauvegarde de l'index et des métadonnées
        faiss.write_index(self.index, f"{VECTOR_INDEX_PATH}.index")
        
        # Sauvegarde des métadonnées des articles
        self.article_data = df
        with open(f"{VECTOR_INDEX_PATH}_metadata.pkl", 'wb') as f:
            pickle.dump(df, f)
        
        print(f"Index créé avec succès: {len(df)} articles indexés")
    
    def load_index(self):
        """Chargement de l'index existant"""
        try:
            self.index = faiss.read_index(f"{VECTOR_INDEX_PATH}.index")
            with open(f"{VECTOR_INDEX_PATH}_metadata.pkl", 'rb') as f:
                self.article_data = pickle.load(f)
            print(f"Index chargé: {len(self.article_data)} articles")
            return True
        except FileNotFoundError:
            print("Index non trouvé. Création nécessaire.")
            return False
    
    def search(self, query, top_k=10, year_filter=None, author_filter=None):
        """Recherche sémantique"""
        if self.index is None:
            if not self.load_index():
                print("Index non disponible")
                return []
        
        # Génération de l'embedding de la requête
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Recherche dans l'index
        scores, indices = self.index.search(query_embedding.astype(np.float32), min(top_k * 3, len(self.article_data)))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # Pas de résultat
                continue
            
            article = self.article_data.iloc[idx]
            
            # Application des filtres
            if year_filter and article['publication_date']:
                try:
                    article_year = int(str(article['publication_date'])[:4])
                    if article_year != year_filter:
                        continue
                except:
                    pass
            
            if author_filter and author_filter.lower() not in str(article.get('authors', '')).lower():
                continue
            
            result = {
                'id': article['id'],
                'scopus_id': article['scopus_id'],
                'title': article['title'],
                'abstract': article['abstract'][:500] + "..." if len(article['abstract']) > 500 else article['abstract'],
                'journal': article['journal'],
                'publication_date': article['publication_date'],
                'keywords': article['keywords'],
                'similarity_score': float(score)
            }
            results.append(result)
            
            if len(results) >= top_k:
                break
        
        return results
    
    def get_article_details(self, article_id):
        """Récupération des détails complets d'un article"""
        conn = sqlite3.connect(self.db_path)
        
        # Article principal
        article_query = '''
            SELECT * FROM articles WHERE id = ?
        '''
        article = pd.read_sql_query(article_query, conn, params=[article_id])
        
        if article.empty:
            return None
        
        # Auteurs
        authors_query = '''
            SELECT a.name, a.auid
            FROM authors a
            JOIN article_authors aa ON a.id = aa.author_id
            WHERE aa.article_id = ?
        '''
        authors = pd.read_sql_query(authors_query, conn, params=[article_id])
        
        conn.close()
        
        article_data = article.iloc[0].to_dict()
        article_data['authors'] = authors.to_dict('records') if not authors.empty else []
        
        return article_data

# Exemple d'utilisation
if __name__ == "__main__":
    search_engine = SemanticSearch()
    
    # Création de l'index (à faire une seule fois)
    search_engine.create_embeddings()
    
    # Test de recherche
    results = search_engine.search("machine learning algorithms", top_k=5)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"Journal: {result['journal']}")
        print(f"Score: {result['similarity_score']:.3f}")
        print(f"Résumé: {result['abstract'][:200]}...")