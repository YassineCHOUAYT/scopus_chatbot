import re
from semantic_search import SemanticSearch
import sqlite3
from config import DATABASE_PATH

class ScopusChatbot:
    def __init__(self):
        self.search_engine = SemanticSearch()
        self.search_engine.load_index()
        self.db_path = DATABASE_PATH
        
        # Patterns pour extraction d'entités
        self.year_pattern = r'\b(19|20)\d{2}\b'
        self.author_pattern = r'(?:by|author|écrit par|de)\s+([A-Za-z\s]+?)(?:\s|$|,|\.|;)'
        
        # Intentions prédéfinies
        self.intents = {
            'search': ['recherche', 'trouve', 'cherche', 'search', 'find', 'look for'],
            'summary': ['résume', 'résumé', 'summary', 'summarize', 'synthèse'],
            'stats': ['statistiques', 'stats', 'nombre', 'combien', 'statistics', 'count'],
            'latest': ['récent', 'dernier', 'nouveau', 'latest', 'recent', 'new'],
            'author': ['auteur', 'écrivain', 'author', 'researcher', 'chercheur']
        }
    
    def extract_intent(self, query):
        """Extraction de l'intention de la requête"""
        query_lower = query.lower()
        
        for intent, keywords in self.intents.items():
            if any(keyword in query_lower for keyword in keywords):
                return intent
        
        return 'search'  # Par défaut
    
    def extract_entities(self, query):
        """Extraction des entités (année, auteur)"""
        entities = {}
        
        # Extraction année
        year_match = re.search(self.year_pattern, query)
        if year_match:
            entities['year'] = int(year_match.group())
        
        # Extraction auteur
        author_match = re.search(self.author_pattern, query, re.IGNORECASE)
        if author_match:
            entities['author'] = author_match.group(1).strip()
        
        return entities
    
    def get_statistics(self):
        """Statistiques générales de la base"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Nombre total d'articles
        cursor.execute("SELECT COUNT(*) FROM articles")
        stats['total_articles'] = cursor.fetchone()[0]
        
        # Nombre d'auteurs
        cursor.execute("SELECT COUNT(*) FROM authors")
        stats['total_authors'] = cursor.fetchone()[0]
        
        # Articles par année (top 5)
        cursor.execute('''
            SELECT SUBSTR(publication_date, 1, 4) as year, COUNT(*) as count
            FROM articles
            WHERE publication_date IS NOT NULL
            GROUP BY year
            ORDER BY count DESC
            LIMIT 5
        ''')
        stats['top_years'] = cursor.fetchall()
        
        # Revues les plus fréquentes
        cursor.execute('''
            SELECT journal, COUNT(*) as count
            FROM articles
            WHERE journal IS NOT NULL AND journal != ''
            GROUP BY journal
            ORDER BY count DESC
            LIMIT 5
        ''')
        stats['top_journals'] = cursor.fetchall()
        
        conn.close()
        return stats
    
    def format_article_response(self, articles, query_type='search'):
        """Formatage de la réponse avec les articles"""
        if not articles:
            return "Désolé, je n'ai trouvé aucun article correspondant à votre recherche."
        
        response = f"J'ai trouvé {len(articles)} article(s) pertinent(s) :\n\n"
        
        for i, article in enumerate(articles, 1):
            response += f"**{i}. {article['title']}**\n"
            response += f"📖 Journal: {article['journal']}\n"
            response += f"📅 Date: {article['publication_date']}\n"
            
            if article.get('keywords'):
                response += f"🏷️ Mots-clés: {article['keywords'][:100]}...\n"
            
            response += f"📄 Résumé: {article['abstract'][:300]}...\n"
            response += f"🔗 Scopus ID: {article['scopus_id']}\n"
            response += f"⭐ Score de pertinence: {article['similarity_score']:.2f}\n\n"
            response += "---\n\n"
        
        return response
    
    def format_stats_response(self, stats):
        """Formatage de la réponse statistiques"""
        response = "📊 **Statistiques de la base Scopus :**\n\n"
        response += f"📚 Total d'articles: {stats['total_articles']:,}\n"
        response += f"👥 Total d'auteurs: {stats['total_authors']:,}\n\n"
        
        response += "📈 **Années les plus productives :**\n"
        for year, count in stats['top_years']:
            response += f"• {year}: {count:,} articles\n"
        
        response += "\n📖 **Revues les plus fréquentes :**\n"
        for journal, count in stats['top_journals']:
            response += f"• {journal}: {count:,} articles\n"
        
        return response
    
    def process_query(self, query):
        """Traitement principal de la requête"""
        if not query.strip():
            return "Posez-moi une question sur les publications scientifiques !"
        
        # Extraction intention et entités
        intent = self.extract_intent(query)
        entities = self.extract_entities(query)
        
        # Traitement selon l'intention
        if intent == 'stats':
            stats = self.get_statistics()
            return self.format_stats_response(stats)
        
        elif intent in ['search', 'latest', 'author', 'summary']:
            # Paramètres de recherche
            top_k = 3 if intent == 'summary' else 10
            year_filter = entities.get('year')
            author_filter = entities.get('author')
            
            # Recherche sémantique
            results = self.search_engine.search(
                query, 
                top_k=top_k, 
                year_filter=year_filter,
                author_filter=author_filter
            )
            
            return self.format_article_response(results, intent)
        
        else:
            # Recherche par défaut
            results = self.search_engine.search(query, top_k=5)
            return self.format_article_response(results)
    
    def get_article_details(self, scopus_id):
        """Récupération des détails d'un article"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM articles WHERE scopus_id = ?", (scopus_id,))
        article = cursor.fetchone()
        
        if not article:
            return "Article non trouvé."
        
        # Récupération des auteurs
        cursor.execute('''
            SELECT a.name
            FROM authors a
            JOIN article_authors aa ON a.id = aa.author_id
            JOIN articles art ON aa.article_id = art.id
            WHERE art.scopus_id = ?
        ''', (scopus_id,))
        
        authors = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Formatage détaillé
        response = f"**{article[2]}**\n\n"  # title
        response += f"👥 **Auteurs:** {', '.join(authors) if authors else 'Non spécifié'}\n"
        response += f"📖 **Journal:** {article[5]}\n"  # journal
        response += f"📅 **Date:** {article[4]}\n"  # publication_date
        
        if article[6]:  # doi
            response += f"🔗 **DOI:** {article[6]}\n"
        
        if article[7]:  # keywords
            response += f"🏷️ **Mots-clés:** {article[7]}\n"
        
        response += f"\n📄 **Résumé complet:**\n{article[3]}\n"  # abstract
        
        return response

# Exemple d'utilisation
if __name__ == "__main__":
    chatbot = ScopusChatbot()
    
    # Tests
    test_queries = [
        "Trouve des articles sur l'intelligence artificielle",
        "Statistiques de la base",
        "Articles récents sur machine learning en 2023",
        "Recherche par auteur Smith"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Requête: {query}")
        print("📝 Réponse:")
        print(chatbot.process_query(query))
        print("\n" + "="*50)