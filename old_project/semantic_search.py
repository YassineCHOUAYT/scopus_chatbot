import json
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from config import get_connection

# Load the same model used for creating embeddings
MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

def fetch_articles_with_embeddings():
    """Fetch all articles with their embeddings from database"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Select all articles that have embeddings
        cursor.execute("""
            SELECT id, title, abstract, authors, published, updated, 
                   link, primary_category, category, doi, journal_ref, embedding
            FROM articles 
            WHERE embedding IS NOT NULL
        """)
        
        articles = cursor.fetchall()
        
        # Convert embedding JSON back to numpy array
        for article in articles:
            if article['embedding']:
                try:
                    embedding_list = json.loads(article['embedding'])
                    article['embedding'] = np.array(embedding_list)
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"⚠️ Error parsing embedding for article {article['id']}: {e}")
                    article['embedding'] = None
        
        return articles
        
    except Exception as e:
        print(f"❌ Error fetching articles: {e}")
        return []
        
    finally:
        cursor.close()
        conn.close()

def semantic_search(query, top_k=10):
    """Perform semantic search on stored articles"""
    print(f"🔍 Searching for: {query}")
    
    # Get query embedding
    query_embedding = model.encode([query])
    
    # Fetch articles with embeddings
    articles = fetch_articles_with_embeddings()
    
    if not articles:
        print("❌ No articles with embeddings found in database")
        return []
    
    print(f"📊 Found {len(articles)} articles with embeddings")
    
    # Calculate similarities
    similarities = []
    valid_articles = []
    
    for article in articles:
        if article['embedding'] is not None:
            try:
                # Calculate cosine similarity
                similarity = cosine_similarity(
                    query_embedding, 
                    article['embedding'].reshape(1, -1)
                )[0][0]
                similarities.append(similarity)
                valid_articles.append(article)
            except Exception as e:
                print(f"⚠️ Error calculating similarity for article {article['id']}: {e}")
                continue
    
    if not similarities:
        print("❌ No valid embeddings found")
        return []
    
    # Sort by similarity
    sorted_indices = np.argsort(similarities)[::-1]
    
    # Return top-k results
    results = []
    for i in sorted_indices[:top_k]:
        article = valid_articles[i]
        results.append({
            'id': article['id'],
            'title': article['title'],
            'abstract': article['abstract'] or '',
            'authors': article['authors'] or '',
            'published': article['published'] or '',
            'updated': article['updated'],
            'link': article['link'] or '',
            'primary_category': article['primary_category'] or '',
            'category': article['category'] or '',
            'doi': article['doi'] or '',
            'journal_ref': article['journal_ref'] or '',
            'score': float(similarities[i])  # Convert to float for JSON serialization
        })
    
    return results

def test_semantic_search():
    """Test the semantic search functionality"""
    query = "machine learning"
    results = semantic_search(query, top_k=5)
    
    print(f"\n🔍 Search results for '{query}':")
    print("=" * 50)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   Similarity: {result['score']:.3f}")
        print(f"   Authors: {result['authors']}")
        print(f"   Published: {result['published']}")
        if result['abstract']:
            print(f"   Abstract: {result['abstract'][:200]}...")

if __name__ == "__main__":
    test_semantic_search()