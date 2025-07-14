import faiss
import json
import numpy as np
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
import re

class ScopusChatbot:
    def __init__(self, index_path="arxiv_index.faiss", metadata_path="arxiv_metadata.json"):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.read_index(index_path)
        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
        
        # Dictionnaire des mots-clés pour différents types de requêtes
        self.keywords = {
            "recent_articles": {
                "fr": ["articles récents", "publications récentes", "nouveaux articles", "derniers travaux", 
                       "récent", "nouveau", "dernière publication", "actualités scientifiques", "publications actuelles", "travaux récents"],
                "en": ["recent articles", "latest publications", "new articles", "recent works", 
                       "recent", "new", "latest", "current research", "fresh publications", "newest papers"]
            },
            "author_search": {
                "fr": ["travaux de", "publications de", "articles de", "recherches de", "auteur", 
                       "chercheur", "scientifique", "professeur", "œuvres de", "études de"],
                "en": ["works by", "publications by", "articles by", "research by", "author", 
                       "researcher", "scientist", "professor", "studies by", "papers by"]
            },
            "statistics": {
                "fr": ["statistiques", "nombre d'articles", "total articles", "comptage", "données", 
                       "chiffres", "métriques", "quantité", "volume", "nombre total"],
                "en": ["statistics", "number of articles", "total articles", "count", "data", 
                       "figures", "metrics", "quantity", "volume", "total number"]
            },
            "ai_medicine": {
                "fr": ["intelligence artificielle", "médecine", "santé", "diagnostic", "traitement", 
                       "IA médicale", "algorithmes médicaux", "apprentissage automatique", "deep learning", "machine learning"],
                "en": ["artificial intelligence", "medicine", "health", "diagnosis", "treatment", 
                       "medical AI", "medical algorithms", "machine learning", "deep learning", "healthcare AI"]
            },
            "computer_science": {
                "fr": ["informatique", "programmation", "algorithmes", "logiciel", "système", 
                       "ordinateur", "technologie", "code", "développement", "ingénierie"],
                "en": ["computer science", "programming", "algorithms", "software", "system", 
                       "computer", "technology", "code", "development", "engineering"]
            },
            "biology": {
                "fr": ["biologie", "génétique", "cellule", "organisme", "évolution", 
                       "biochimie", "biotechnologie", "microbiologie", "physiologie", "écologie"],
                "en": ["biology", "genetics", "cell", "organism", "evolution", 
                       "biochemistry", "biotechnology", "microbiology", "physiology", "ecology"]
            },
            "physics": {
                "fr": ["physique", "quantique", "particule", "énergie", "matière", 
                       "théorie", "expérience", "mécanique", "thermodynamique", "optique"],
                "en": ["physics", "quantum", "particle", "energy", "matter", 
                       "theory", "experiment", "mechanics", "thermodynamics", "optics"]
            },
            "chemistry": {
                "fr": ["chimie", "molécule", "réaction", "composé", "synthèse", 
                       "catalyse", "organique", "inorganique", "analytique", "physico-chimie"],
                "en": ["chemistry", "molecule", "reaction", "compound", "synthesis", 
                       "catalysis", "organic", "inorganic", "analytical", "physical chemistry"]
            }
        }

    def extract_keywords_from_query(self, query):
        """Extrait et suggère des mots-clés basés sur la requête"""
        query_lower = query.lower()
        detected_keywords = []
        
        for category, keywords in self.keywords.items():
            for lang in ["fr", "en"]:
                for keyword in keywords[lang]:
                    if keyword in query_lower:
                        detected_keywords.extend(keywords[lang][:5])  # Prendre les 5 premiers
                        break
                if detected_keywords:
                    break
        
        return list(set(detected_keywords))

    def enhance_query_with_keywords(self, query):
        """Améliore la requête avec des mots-clés pertinents"""
        base_keywords = self.extract_keywords_from_query(query)
        
        if len(base_keywords) < 10:
            generic_keywords = [
                "research", "study", "analysis", "investigation", "publication",
                "recherche", "étude", "analyse", "investigation", "publication"
            ]
            base_keywords.extend(generic_keywords[:10-len(base_keywords)])
        
        return base_keywords[:10]

    def process_query(self, query):
        """Traite la requête avec amélioration par mots-clés"""
        query = query.lower()
        keywords = self.enhance_query_with_keywords(query)
        
        print(f"🔍 Mots-clés détectés: {', '.join(keywords)}")
        
        recent_patterns = ["articles récents", "recent articles", "publications récentes", "latest publications"]
        if any(pattern in query for pattern in recent_patterns):
            return self.get_recent_articles(), keywords

        author_patterns = ["travaux de", "works by", "publications de", "articles de", "research by"]
        for pattern in author_patterns:
            if pattern in query:
                name = query.split(pattern)[-1].strip()
                return self.get_articles_by_author(name), keywords

        stats_patterns = ["statistiques", "statistics", "nombre d'articles", "number of articles", "total articles"]
        if any(pattern in query for pattern in stats_patterns):
            return self.get_stats(), keywords

        enhanced_query = query + " " + " ".join(keywords)
        return self.semantic_search(enhanced_query), keywords

    def semantic_search(self, query, k=5):
        """Recherche sémantique améliorée"""
        q_emb = self.model.encode([query])
        _, I = self.index.search(np.array(q_emb).astype("float32"), k)
        return [self.metadata[i] for i in I[0] if i < len(self.metadata)]

    def get_articles_by_author(self, name):
        """Recherche d'articles par auteur avec recherche flexible"""
        name = name.lower().strip()
        result = []
        
        for art in self.metadata:
            authors = art.get("authors", [])
            for author in authors:
                author_name = author.get("name", "").lower()
                if name in author_name or any(part in author_name for part in name.split()):
                    result.append(art)
                    break
        
        return result

    def get_recent_articles(self, days=30):
        """Récupère les articles récents avec gestion d'erreurs"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_articles = []
        
        for article in self.metadata:
            if "published_date" in article:
                try:
                    pub_date = datetime.strptime(article["published_date"], "%Y-%m-%d")
                    if pub_date >= cutoff:
                        recent_articles.append(article)
                except ValueError:
                    continue
        
        return recent_articles

    def get_stats(self):
        """Statistiques détaillées"""
        author_names = set()
        categories = {}
        years = {}
        
        for art in self.metadata:
            for a in art.get("authors", []):
                if isinstance(a, dict) and "name" in a:
                    author_names.add(a["name"])
            
            category = art.get("category", "Unknown")
            categories[category] = categories.get(category, 0) + 1
            
            if "published_date" in art:
                try:
                    year = datetime.strptime(art["published_date"], "%Y-%m-%d").year
                    years[year] = years.get(year, 0) + 1
                except ValueError:
                    pass
        
        return {
            "total_articles": len(self.metadata),
            "authors_count": len(author_names),
            "categories": categories,
            "years": years
        }

    def search_by_topic(self, topic):
        """Recherche par sujet avec mots-clés étendus"""
        topic_keywords = self.enhance_query_with_keywords(topic)
        enhanced_query = topic + " " + " ".join(topic_keywords)
        return self.semantic_search(enhanced_query)

    def get_trending_topics(self):
        """Identifie les sujets tendance basés sur les mots-clés"""
        word_freq = {}
        
        for art in self.metadata:
            title = art.get("title", "").lower()
            abstract = art.get("abstract", "").lower()
            
            words = re.findall(r'\b\w+\b', title + " " + abstract)
            for word in words:
                if len(word) > 4:
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]

    def get_articles_about_keyword(self, keyword):
        """Retourne les articles contenant un mot-clé dans le titre ou résumé"""
        keyword = keyword.lower()
        results = []
        for art in self.metadata:
            title = art.get("title", "").lower()
            abstract = art.get("abstract", "").lower()
            if keyword in title or keyword in abstract:
                results.append(art)
        return results

def main():
    try:
        chatbot = ScopusChatbot()

        print("🔍 Résultat recherche sémantique améliorée :")
        result, keywords = chatbot.process_query("intelligence artificielle et médecine")
        print(f"Mots-clés utilisés: {keywords}")
        for article in result[:3]:
            print(f"- {article.get('title', 'Titre non disponible')}")

        print("\n📅 Articles publiés récemment :")
        recent_articles, keywords = chatbot.process_query("articles récents")
        print(f"Mots-clés utilisés: {keywords}")
        for article in recent_articles[:3]:
            print(f"- {article.get('title', 'Titre non disponible')} ({article.get('published_date', '?')})")

        print("\n👨‍🔬 Travaux de 'Helen Qu' :")
        works, keywords = chatbot.process_query("travaux de Helen Qu")
        print(f"Mots-clés utilisés: {keywords}")
        for article in works[:3]:
            print(f"- {article.get('title', 'Titre non disponible')}")

        print("\n📊 Statistiques :")
        stats, keywords = chatbot.process_query("statistiques")
        print(f"Mots-clés utilisés: {keywords}")
        print(f"- Nombre total d'articles : {stats['total_articles']}")
        print(f"- Nombre d'auteurs uniques : {stats['authors_count']}")

        print("\n🔥 Sujets tendance :")
        trending = chatbot.get_trending_topics()
        for word, freq in trending[:10]:
            print(f"- {word}: {freq} occurrences")

        # Nouveauté : articles sur "machine learning"
        print("\n📚 Articles sur 'machine learning' :")
        ml_articles = chatbot.get_articles_about_keyword("machine learning")
        seen_titles = set()
        for article in ml_articles[:10]:
            title = article.get('title', 'Titre inconnu')
            if title not in seen_titles:
                print(f"- {title} ({article.get('published_date', '?')})")
                seen_titles.add(title)

        print("\n🧠 Tests de requêtes variées :")
        test_queries = [
            "deep learning et biologie",
            "quantum computing",
            "machine learning applications",
            "recherche en informatique",
            "intelligence artificielle médicale",
            "publications en chimie",
            "physique quantique",
            "biotechnologie moderne"
        ]
        
        for query in test_queries:
            print(f"\n🔎 Requête : {query}")
            result, keywords = chatbot.process_query(query)
            print(f"Mots-clés: {', '.join(keywords)}")
            if isinstance(result, list):
                print(f"Résultats trouvés: {len(result)}")
                for art in result[:2]:
                    print(f"- {art.get('title', 'Titre inconnu')}")
            else:
                print(result)

    except FileNotFoundError as e:
        print(f"❌ Fichier manquant : {e}")
        print("💡 Assurez-vous que les fichiers arxiv_index.faiss et arxiv_metadata.json existent")
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de lecture du JSON : {e}")
    except Exception as e:
        print(f"❌ Une erreur inattendue est survenue : {e}")

if __name__ == "__main__":
    main()
