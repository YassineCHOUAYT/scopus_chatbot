import json
import pickle
import numpy as np
from config import get_connection

EMBEDDINGS_FILE = "data/embeddings.pkl"

def load_embeddings():
    """Load embeddings from pickle file"""
    try:
        with open(EMBEDDINGS_FILE, 'rb') as f:
            data = pickle.load(f)
        return data
    except FileNotFoundError:
        print(f"❌ Fichier '{EMBEDDINGS_FILE}' introuvable. Lance d'abord `embedding.py`.")
        return None
    except Exception as e:
        print(f"❌ Erreur lors du chargement des embeddings: {e}")
        return None

def update_articles_with_embeddings(data):
    """Update articles in database with their embeddings"""
    conn = get_connection()
    cursor = conn.cursor()
    
    articles = data['articles']
    embeddings = data['embeddings']
    
    if len(articles) != len(embeddings):
        print("❌ Nombre d'articles et d'embeddings différent!")
        return
    
    success_count = 0
    
    for i, article in enumerate(articles):
        try:
            # Convert numpy array to list for JSON storage
            embedding_list = embeddings[i].tolist()
            embedding_json = json.dumps(embedding_list)
            
            cursor.execute("""
                UPDATE articles 
                SET embedding = %s 
                WHERE id = %s
            """, (embedding_json, article['id']))
            
            if cursor.rowcount > 0:
                success_count += 1
                print(f"✅ Embedding ajouté pour: {article['title'][:50]}...")
            else:
                print(f"⚠️ Article non trouvé en base: {article['id']}")
                
        except Exception as e:
            print(f"❌ Erreur lors de l'update de l'article {article['id']}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ {success_count}/{len(articles)} articles mis à jour avec leurs embeddings.")

def main():
    print("📥 Chargement des embeddings...")
    data = load_embeddings()
    
    if data is None:
        return
    
    print(f"📊 {len(data['articles'])} articles avec embeddings chargés")
    
    # Update database with embeddings
    update_articles_with_embeddings(data)
    
    print("✅ Processus terminé!")

if __name__ == "__main__":
    main()