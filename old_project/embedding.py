import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle

INPUT_FILE = "data/scopus_articles.json"
OUTPUT_FILE = "data/embeddings.pkl"
MODEL_NAME = "all-MiniLM-L6-v2"  # Fast and efficient model

def load_articles(filepath):
    """Load articles from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        print(f"✅ {len(articles)} articles chargés depuis {filepath}")
        return articles
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {filepath}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Erreur JSON: {e}")
        return []

def prepare_texts_for_embedding(articles):
    """Prepare texts for embedding, handling empty abstracts"""
    texts = []
    valid_articles = []
    
    for article in articles:
        title = article.get('title', '').strip()
        abstract = article.get('abstract', '').strip()
        
        # Use abstract if available, otherwise use title
        if abstract:
            text = f"{title}\n\n{abstract}"
        elif title:
            text = title
        else:
            print(f"⚠️ Article sans titre ni abstract: {article.get('id', 'unknown')}")
            continue
            
        texts.append(text)
        valid_articles.append(article)
        
    print(f"📝 {len(texts)} textes préparés pour l'embedding")
    return texts, valid_articles

def create_embeddings(texts, model_name=MODEL_NAME):
    """Create embeddings for the texts"""
    print(f"🤖 Chargement du modèle {model_name}...")
    model = SentenceTransformer(model_name)
    
    print("⚡ Création des embeddings...")
    embeddings = model.encode(texts, show_progress_bar=True)
    
    print(f"✅ {len(embeddings)} embeddings créés")
    return embeddings

def save_embeddings(articles, embeddings, texts, filepath):
    """Save articles, embeddings, and texts to pickle file"""
    data = {
        'articles': articles,
        'embeddings': embeddings,
        'texts': texts,
        'model_name': MODEL_NAME
    }
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'wb') as f:
        pickle.dump(data, f)
    
    print(f"💾 Données sauvegardées dans {filepath}")

def main():
    print("📥 Chargement des articles...")
    articles = load_articles(INPUT_FILE)
    
    if not articles:
        print("❌ Aucun article à encoder.")
        return
    
    print(f"📊 Articles chargés: {len(articles)}")
    
    # Show some stats
    articles_with_abstract = [a for a in articles if a.get('abstract', '').strip()]
    articles_with_title = [a for a in articles if a.get('title', '').strip()]
    
    print(f"📝 Articles avec abstract: {len(articles_with_abstract)}")
    print(f"📰 Articles avec titre: {len(articles_with_title)}")
    
    # Prepare texts for embedding
    texts, valid_articles = prepare_texts_for_embedding(articles)
    
    if not texts:
        print("❌ Aucun texte valide pour l'embedding.")
        return
    
    # Create embeddings
    embeddings = create_embeddings(texts)
    
    # Save everything
    save_embeddings(valid_articles, embeddings, texts, OUTPUT_FILE)
    
    print("✅ Processus terminé avec succès!")

if __name__ == "__main__":
    main()