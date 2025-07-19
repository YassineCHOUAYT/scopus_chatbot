import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import re
from typing import List, Tuple, Dict, Any, Optional
from difflib import SequenceMatcher
import unicodedata
from collections import defaultdict

class EnhancedArticleSearcher:
    def __init__(self, index_path: str, metadata_path: str, model_name: str = "all-MiniLM-L6-v2"):
        """Initialise le moteur de recherche amélioré."""
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.index = None
        self.metadata = None
        self.model = None
        self.all_authors_cache = None
        self.author_articles_map = None
        self.category_map = None
        
        print("🔄 Initialisation du moteur de recherche amélioré...")
        self.load_resources(model_name)
        
    def load_resources(self, model_name: str):
        """Charge toutes les ressources nécessaires."""
        try:
            print("📊 Chargement de l'index FAISS...")
            self.index = faiss.read_index(self.index_path)

            print("📋 Chargement des métadonnées...")
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

            print("🤖 Chargement du modèle de vectorisation...")
            self.model = SentenceTransformer(model_name)
            
            print(f"✅ Base de données chargée: {len(self.metadata)} articles")
            self._build_author_mapping()
            self._build_category_mapping()
            
        except FileNotFoundError as e:
            print(f"❌ Erreur: Fichier non trouvé - {e}")
            raise
        except Exception as e:
            print(f"❌ Erreur lors du chargement: {e}")
            raise

    def _build_author_mapping(self):
        """Construit un mapping auteur -> articles pour des recherches rapides."""
        self.author_articles_map = defaultdict(list)
        self.all_authors_cache = set()
        
        for idx, article in enumerate(self.metadata):
            for author in article.get("authors", []):
                name = author.get("name", "").strip()
                if name:
                    normalized_name = self.normalize_text(name)
                    self.author_articles_map[normalized_name].append(idx)
                    self.all_authors_cache.add(name)
        
        self.all_authors_cache = sorted(self.all_authors_cache)
        print(f"📚 {len(self.all_authors_cache)} auteurs uniques indexés")

    def _build_category_mapping(self):
        """Construit un mapping catégorie -> articles."""
        self.category_map = defaultdict(list)
        
        for idx, article in enumerate(self.metadata):
            for category in article.get("categories", []):
                self.category_map[category].append(idx)
        
        print(f"🏷️  {len(self.category_map)} catégories uniques indexées")

    def normalize_text(self, text: str) -> str:
        """Normalise le texte pour améliorer les correspondances."""
        if not text:
            return ""
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        return text.lower().strip()

    def detect_search_type(self, query: str) -> Dict[str, Any]:
        """
        Détecte automatiquement le type de recherche basé sur la requête.
        Version améliorée avec plus de patterns et meilleure précision.
        """
        query_lower = query.lower()
        search_info = {
            'type': 'general',
            'authors': [],
            'keywords': query.strip(),
            'confidence': 0.0,
            'year_filter': None
        }
        
        # Détection d'année (ex: "2020", "2015-2020")
        year_match = re.search(r'(19|20)\d{2}(?:\s*-\s*(19|20)\d{2})?', query)
        if year_match:
            search_info['year_filter'] = year_match.group()
            search_info['keywords'] = re.sub(r'(19|20)\d{2}(?:\s*-\s*(19|20)\d{2})?', '', search_info['keywords']).strip()
        
        # Mots-clés indiquant une recherche par auteur
        author_indicators = [
            'par', 'de', 'd\'', 'by', 'author', 'auteur', 'écrit par', 'written by',
            'articles de', 'papers by', 'travaux de', 'publications de',
            'recherche de', 'études de', 'works of', 'œuvres de'
        ]
        
        # Vérifie si c'est une recherche par auteur
        has_author_indicator = any(indicator in query_lower for indicator in author_indicators)
        
        if has_author_indicator:
            authors = self._extract_author_names(query)
            if authors:
                search_info['type'] = 'mixed' if len(query.split()) > len(' '.join(authors).split()) + 2 else 'author'
                search_info['authors'] = authors
                search_info['confidence'] = 0.9
                
                # Nettoie les mots-clés
                cleaned_query = query
                for indicator in author_indicators:
                    cleaned_query = re.sub(rf'\b{re.escape(indicator)}\b', '', cleaned_query, flags=re.IGNORECASE)
                for author in authors:
                    cleaned_query = re.sub(rf'\b{re.escape(author)}\b', '', cleaned_query, flags=re.IGNORECASE)
                
                search_info['keywords'] = re.sub(r'\s+', ' ', cleaned_query).strip()
        else:
            # Vérifie si la requête contient des noms probables d'auteurs
            potential_authors = self._find_potential_authors_in_query(query)
            if potential_authors:
                search_info['type'] = 'mixed'
                search_info['authors'] = potential_authors
                search_info['confidence'] = 0.7
                search_info['keywords'] = ' '.join([w for w in query.split() 
                                                  if not any(a.lower() in w.lower() for a in potential_authors)]).strip()
        
        return search_info

    def _extract_author_names(self, query: str) -> List[str]:
        """Extrait les noms d'auteurs de la requête avec patterns améliorés."""
        authors = []
        excluded_words = {
            'les', 'des', 'de', 'le', 'la', 'du', 'articles', 'article', 'sur', 
            'par', 'avec', 'dans', 'pour', 'que', 'qui', 'sont', 'est', 'une', 'un',
            'recherche', 'etude', 'paper', 'papers', 'study', 'research', 'work',
            'results', 'analysis', 'method', 'approach', 'technique', 'model', 'et', 'and'
        }
        
        # Patterns améliorés pour extraction
        patterns = [
            r'(?:par|de|d\'|by|author|auteur|écrit par|written by|works of|œuvres de)\s+([A-ZÀ-Ü][a-zà-üß-ÿ]+(?:\s+[A-ZÀ-Ü][a-zà-üß-ÿ]+)*)',
            r'(?:articles de|papers by|travaux de|publications de|works of)\s+([A-ZÀ-Ü][a-zà-üß-ÿ]+(?:\s+[A-ZÀ-Ü][a-zà-üß-ÿ]+)*)',
            r'\b([A-ZÀ-Ü]\.\s*[A-ZÀ-Ü][a-zà-üß-ÿ]+)\b',  # J. Doe
            r'\b([A-ZÀ-Ü][a-zà-üß-ÿ]+\s+et\s+al\.?)\b',  # Smith et al.
            r'\b([A-ZÀ-Ü][a-zà-üß-ÿ]+\s+(?:[A-ZÀ-Ü][a-zà-üß-ÿ.]+(?:\s+[A-ZÀ-Ü][a-zà-üß-ÿ.]+)*)\b'  # Noms complets
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                author_name = match.group(1).strip()
                if self._is_valid_author_name(author_name, excluded_words):
                    if author_name not in authors:
                        authors.append(author_name)
        
        return authors

    def _find_potential_authors_in_query(self, query: str) -> List[str]:
        """Trouve des auteurs potentiels en utilisant le mapping d'auteurs."""
        potential_authors = []
        query_words = query.split()
        
        # Vérifie les noms complets (2-3 mots)
        for i in range(len(query_words)):
            for j in range(i+1, min(i+4, len(query_words)+1)):
                potential_name = ' '.join(query_words[i:j])
                normalized_name = self.normalize_text(potential_name)
                
                # Vérifie directement dans le mapping
                if normalized_name in self.author_articles_map:
                    # Trouve la version originale avec la casse correcte
                    for author in self.all_authors_cache:
                        if self.normalize_text(author) == normalized_name:
                            potential_authors.append(author)
                            break
        
        return list(set(potential_authors))

    def _is_valid_author_name(self, name: str, excluded_words: set) -> bool:
        """Valide si une chaîne est probablement un nom d'auteur."""
        if not name or len(name) < 2:
            return False
        
        words = name.lower().split()
        
        # Vérifie les mots exclus
        if any(word in excluded_words for word in words):
            return False
        
        # Au moins un mot doit avoir plus de 1 caractère
        if not any(len(word) > 1 for word in words):
            return False
        
        # Ne doit pas contenir que des chiffres ou caractères spéciaux
        if all(not c.isalpha() for c in name):
            return False
        
        return True

    def find_matching_authors(self, query_authors: List[str], article_authors: List[Dict]) -> Tuple[bool, List[str]]:
        """Trouve les correspondances entre auteurs avec seuil de similarité ajustable."""
        if not query_authors or not article_authors:
            return False, []
        
        matched_authors = []
        
        for query_author in query_authors:
            query_norm = self.normalize_text(query_author)
            
            for article_author in article_authors:
                author_name = article_author.get("name", "")
                if not author_name:
                    continue
                    
                author_norm = self.normalize_text(author_name)
                
                # Correspondance exacte
                if query_norm == author_norm:
                    matched_authors.append(author_name)
                    continue
                
                # Un terme contient l'autre
                if query_norm in author_norm or author_norm in query_norm:
                    matched_authors.append(author_name)
                    continue
                
                # Similarité élevée
                similarity = SequenceMatcher(None, query_norm, author_norm).ratio()
                if similarity >= 0.8:
                    matched_authors.append(author_name)
                    continue
                
                # Correspondance du dernier nom (nom de famille)
                query_parts = query_norm.split()
                author_parts = author_norm.split()
                if len(query_parts) > 1 and len(author_parts) > 1:
                    if query_parts[-1] == author_parts[-1]:  # Même nom de famille
                        matched_authors.append(author_name)
        
        return len(matched_authors) > 0, list(set(matched_authors))

    def search_by_author(self, author_name: str, top_k: int = 10) -> List[Dict]:
        """Recherche directe par nom d'auteur en utilisant le mapping pré-calculé."""
        normalized_name = self.normalize_text(author_name)
        article_indices = self.author_articles_map.get(normalized_name, [])
        
        results = []
        for idx in article_indices[:top_k]:
            article = self.metadata[idx]
            results.append({
                'article': article,
                'relevance': 100.0,  # Pertinence maximale pour les recherches directes
                'matched_authors': [a['name'] for a in article.get('authors', []) 
                                  if self.normalize_text(a['name']) == normalized_name]
            })
        
        return results

    def search(self, query: str, top_k: int = 10, search_pool_multiplier: int = 3) -> Dict[str, Any]:
        """
        Fonction de recherche principale améliorée avec gestion des années et recherche directe par auteur.
        """
        if not query.strip():
            return {'results': [], 'search_info': {'type': 'empty'}}
        
        # Analyse la requête
        search_info = self.detect_search_type(query)
        
        # Recherche directe par auteur si type 'author' avec haute confiance
        if search_info['type'] == 'author' and search_info['confidence'] >= 0.8:
            author_results = []
            for author in search_info['authors']:
                author_results.extend(self.search_by_author(author, top_k))
            
            # Trie par date (plus récent d'abord)
            author_results.sort(key=lambda x: x['article'].get('published_date', ''), reverse=True)
            
            return {
                'results': author_results[:top_k],
                'search_info': search_info,
                'total_matches': len(author_results)
            }
        
        # Vectorisation de la requête
        search_query = search_info['keywords'] if search_info['keywords'] else query
        query_embedding = self.model.encode([search_query])
        query_embedding = np.array(query_embedding).astype("float32")
        
        # Recherche dans l'index
        search_pool = top_k * search_pool_multiplier
        distances, indices = self.index.search(query_embedding, search_pool)
        
        # Traitement des résultats
        results = []
        author_matched = []
        other_relevant = []
        
        for dist, idx in zip(distances[0], indices[0]):
            if 0 <= idx < len(self.metadata):
                article = self.metadata[idx]
                relevance_score = max(0, (1 - dist) * 100)
                
                # Filtrage par année si spécifié
                if search_info['year_filter']:
                    article_year = article.get('published_date', '')[:4]
                    if not self._matches_year_filter(article_year, search_info['year_filter']):
                        continue
                
                article_info = {
                    'article': article,
                    'relevance': relevance_score,
                    'matched_authors': []
                }
                
                # Filtre par auteur si nécessaire
                if search_info['authors']:
                    has_match, matched = self.find_matching_authors(
                        search_info['authors'], 
                        article.get('authors', [])
                    )
                    
                    if has_match:
                        article_info['matched_authors'] = matched
                        article_info['relevance'] = min(100, relevance_score * 1.2)  # Boost pour correspondance auteur
                        author_matched.append(article_info)
                    else:
                        other_relevant.append(article_info)
                else:
                    results.append(article_info)
        
        # Combine et trie les résultats
        if search_info['authors']:
            # Priorité aux correspondances d'auteurs
            results = sorted(author_matched, key=lambda x: x['relevance'], reverse=True)[:top_k]
            if len(results) < top_k:
                remaining_slots = top_k - len(results)
                results.extend(sorted(other_relevant, key=lambda x: x['relevance'], reverse=True)[:remaining_slots])
        else:
            results = sorted(results, key=lambda x: x['relevance'], reverse=True)[:top_k]
        
        return {
            'results': results,
            'search_info': search_info,
            'total_author_matches': len(author_matched) if search_info['authors'] else 0,
            'total_other': len(other_relevant) if search_info['authors'] else 0
        }

    def _matches_year_filter(self, article_year: str, year_filter: str) -> bool:
        """Vérifie si l'année de l'article correspond au filtre."""
        if not article_year or not article_year.isdigit():
            return False
        
        if '-' in year_filter:
            start, end = year_filter.split('-')
            return start <= article_year <= end
        else:
            return article_year == year_filter

    def get_articles_by_author(self, author_name: str, limit: int = 10) -> List[Dict]:
        """Retourne tous les articles d'un auteur spécifique."""
        normalized_name = self.normalize_text(author_name)
        article_indices = self.author_articles_map.get(normalized_name, [])
        
        articles = []
        for idx in article_indices[:limit]:
            articles.append(self.metadata[idx])
        
        # Trie par date (plus récent d'abord)
        articles.sort(key=lambda x: x.get('published_date', ''), reverse=True)
        
        return articles

    def get_author_stats(self, author_name: str) -> Dict[str, Any]:
        """Retourne des statistiques pour un auteur spécifique."""
        normalized_name = self.normalize_text(author_name)
        article_indices = self.author_articles_map.get(normalized_name, [])
        
        if not article_indices:
            return None
        
        stats = {
            'author_name': author_name,
            'total_articles': len(article_indices),
            'first_publication': None,
            'last_publication': None,
            'categories': defaultdict(int),
            'coauthors': defaultdict(int)
        }
        
        years = []
        for idx in article_indices:
            article = self.metadata[idx]
            year = article.get('published_date', '')[:4]
            if year:
                years.append(year)
            
            # Catégories
            for cat in article.get('categories', []):
                stats['categories'][cat] += 1
            
            # Co-auteurs
            for author in article.get('authors', []):
                coauthor_name = author.get('name', '')
                if coauthor_name and self.normalize_text(coauthor_name) != normalized_name:
                    stats['coauthors'][coauthor_name] += 1
        
        if years:
            stats['first_publication'] = min(years)
            stats['last_publication'] = max(years)
        
        # Trie les catégories et coauteurs par fréquence
        stats['top_categories'] = sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True)[:5]
        stats['top_coauthors'] = sorted(stats['coauthors'].items(), key=lambda x: x[1], reverse=True)[:5]
        
        return stats

    def display_results(self, search_result: Dict[str, Any]):
        """Affiche les résultats de manière formatée avec plus d'informations."""
        results = search_result['results']
        search_info = search_result['search_info']
        
        if not results:
            print("❌ Aucun résultat trouvé.")
            if search_info['authors']:
                self._suggest_similar_authors(search_info['authors'])
            return
        
        print(f"\n📊 === Résultats trouvés ({len(results)} articles) ===")
        if search_info['year_filter']:
            print(f"   📅 Filtre année: {search_info['year_filter']}")
        
        for i, result_info in enumerate(results, 1):
            article = result_info['article']
            relevance = result_info['relevance']
            matched_authors = result_info['matched_authors']
            
            title = article.get("title", "Titre inconnu")
            year = article.get("published_date", "")[:4] if article.get("published_date") else "Année inconnue"
            doi = article.get("doi", "")
            url = article.get("url", "")
            
            print(f"\n{i}. {title} ({year})")
            print(f"   📈 Pertinence: {relevance:.1f}%")
            
            if doi:
                print(f"   🔗 DOI: {doi}")
            if url:
                print(f"   🌐 URL: {url}")
            
            # Affiche les auteurs avec mise en évidence
            authors_names = [a.get("name", "") for a in article.get("authors", [])]
            if authors_names:
                authors_str = []
                for name in authors_names:
                    if name in matched_authors:
                        authors_str.append(f"✅ {name}")
                    else:
                        authors_str.append(name)
                print(f"   👥 Auteur(s): {', '.join(authors_str)}")
            
            # Affiche le résumé avec mise en évidence des mots-clés
            abstract = article.get("abstract", article.get("summary", ""))
            if abstract:
                highlighted = self._highlight_keywords(abstract, search_info['keywords'])
                truncated = highlighted[:400] + "..." if len(highlighted) > 400 else highlighted
                print(f"   📄 Résumé: {truncated}")
            
            # Catégories avec comptage
            categories = article.get("categories", [])
            if categories:
                print(f"   🏷️  Catégories: {', '.join(categories[:3])}")
        
        # Statistiques avancées
        if search_info['authors']:
            author_matches = search_result.get('total_author_matches', 0)
            other_count = search_result.get('total_other', 0)
            print(f"\n📈 Statistiques: {author_matches} avec correspondance auteur, {other_count} autres résultats pertinents")

    def _highlight_keywords(self, text: str, keywords: str) -> str:
        """Met en évidence les mots-clés dans le texte."""
        if not keywords or not text:
            return text
        
        keyword_list = [k for k in keywords.split() if len(k) > 3]  # Ignore les mots courts
        highlighted = text
        
        for word in keyword_list:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            highlighted = pattern.sub(f"**{word.upper()}**", highlighted)
        
        return highlighted

    def _suggest_similar_authors(self, query_authors: List[str]):
        """Suggère des auteurs similaires avec plus de précision."""
        print(f"\n💡 Suggestions d'auteurs similaires:")
        
        for query_author in query_authors:
            suggestions = []
            query_norm = self.normalize_text(query_author)
            
            # Vérifie d'abord les correspondances partielles dans les noms indexés
            for author in self.all_authors_cache:
                author_norm = self.normalize_text(author)
                
                # Correspondance sur le nom de famille
                query_last = query_norm.split()[-1] if ' ' in query_norm else query_norm
                author_last = author_norm.split()[-1] if ' ' in author_norm else author_norm
                
                if query_last == author_last:
                    suggestions.append((author, 1.0))
                    continue
                
                # Similarité élevée
                similarity = SequenceMatcher(None, query_norm, author_norm).ratio()
                if similarity >= 0.6:
                    suggestions.append((author, similarity))
            
            # Trie et affiche
            suggestions.sort(key=lambda x: x[1], reverse=True)
            
            if suggestions:
                print(f"   Pour '{query_author}':")
                for author, sim in suggestions[:5]:
                    print(f"     - {author} ({sim*100:.0f}% similarité)")
                    # Affiche le nombre d'articles pour aider
                    norm_name = self.normalize_text(author)
                    count = len(self.author_articles_map.get(norm_name, []))
                    print(f"       ({count} articles)")

    def interactive_search(self):
        """Mode de recherche interactive amélioré."""
        print("\n🚀 === Moteur de Recherche d'Articles Scientifiques Amélioré ===")
        print("💡 Ce système détecte automatiquement le type de recherche:")
        print("   • Recherche par auteur: 'articles de Smith', 'par John Doe'")
        print("   • Recherche générale: 'machine learning', 'neural networks'")
        print("   • Recherche mixte: 'deep learning par LeCun'")
        print("   • Filtre année: 'transformers 2018-2020'")
        print("\n📋 Commandes spéciales:")
        print("   • 'help' : Afficher l'aide")
        print("   • 'stats' : Statistiques de la base")
        print("   • 'author <nom>' : Recherche directe par auteur")
        print("   • 'author_stats <nom>' : Statistiques d'un auteur")
        print("   • 'exit' ou 'quit' : Quitter")
        
        while True:
            try:
                query = input("\n🔍 Votre recherche: ").strip()
                
                if query.lower() in ['exit', 'quit', 'q']:
                    print("👋 Au revoir !")
                    break
                    
                elif query.lower() == 'help':
                    self._show_help()
                    continue
                    
                elif query.lower() == 'stats':
                    self._show_stats()
                    continue
                    
                elif query.lower().startswith('author '):
                    author_name = query[7:].strip()
                    if author_name:
                        articles = self.get_articles_by_author(author_name)
                        if articles:
                            print(f"\n📚 Articles de {author_name} ({len(articles)} trouvés):")
                            for i, article in enumerate(articles, 1):
                                title = article.get("title", "Titre inconnu")
                                year = article.get("published_date", "")[:4] if article.get("published_date") else "Année inconnue"
                                print(f"{i}. {title} ({year})")
                        else:
                            print(f"❌ Aucun article trouvé pour {author_name}")
                            self._suggest_similar_authors([author_name])
                    continue
                
                elif query.lower().startswith('author_stats '):
                    author_name = query[12:].strip()
                    if author_name:
                        stats = self.get_author_stats(author_name)
                        if stats:
                            print(f"\n📊 Statistiques pour {stats['author_name']}:")
                            print(f"   📚 Total articles: {stats['total_articles']}")
                            print(f"   📅 Première publication: {stats['first_publication']}")
                            print(f"   📅 Dernière publication: {stats['last_publication']}")
                            
                            print("\n🏷️  Catégories principales:")
                            for cat, count in stats['top_categories']:
                                print(f"   • {cat}: {count} articles")
                            
                            print("\n👥 Principaux collaborateurs:")
                            for coauth, count in stats['top_coauthors']:
                                print(f"   • {coauth}: {count} collaborations")
                        else:
                            print(f"❌ Aucune statistique trouvée pour {author_name}")
                            self._suggest_similar_authors([author_name])
                    continue
                
                elif not query:
                    print("⚠️  Veuillez saisir une requête.")
                    continue
                
                # Recherche standard
                result = self.search(query, top_k=8)
                self.display_results(result)
                
            except KeyboardInterrupt:
                print("\n👋 Recherche interrompue. Au revoir !")
                break
            except Exception as e:
                print(f"❌ Erreur lors de la recherche: {e}")

    def _show_help(self):
        """Affiche l'aide détaillée."""
        print("\n📖 === Aide du Moteur de Recherche Amélioré ===")
        print("\n🎯 Types de recherche supportés:")
        print("   1. Par auteur:")
        print("      • 'articles de Martin'")
        print("      • 'publications par J. Smith'")
        print("      • 'author Jean Dupont' (recherche directe)")
        print("      • 'author_stats Marie Curie' (statistiques auteur)")
        print("\n   2. Par contenu/sujet:")
        print("      • 'machine learning'")
        print("      • 'deep learning applications'")
        print("\n   3. Recherche combinée:")
        print("      • 'transformers par Vaswani 2017'")
        print("      • 'computer vision articles de LeCun 2010-2020'")
        print("\n💡 Conseils avancés:")
        print("   • Utilisez des guillemets pour les phrases exactes")
        print("   • Les noms d'auteurs peuvent être partiels (nom de famille suffit)")
        print("   • Combinez avec des filtres année: 'gan 2018-2020'")

    def _show_stats(self):
        """Affiche des statistiques détaillées de la base."""
        print(f"\n📊 === Statistiques Complètes de la Base ===")
        print(f"   📚 Total articles: {len(self.metadata)}")
        print(f"   👥 Total auteurs uniques: {len(self.all_authors_cache)}")
        print(f"   🏷️  Total catégories uniques: {len(self.category_map)}")
        
        # Auteurs les plus prolifiques
        prolific_authors = sorted(
            [(author, len(articles)) for author, articles in self.author_articles_map.items()],
            key=lambda x: x[1], reverse=True
        )[:5]
        
        print("\n🏆 Auteurs les plus prolifiques:")
        for author, count in prolific_authors:
            print(f"   • {author}: {count} articles")
        
        # Catégories les plus populaires
        popular_categories = sorted(
            [(cat, len(articles)) for cat, articles in self.category_map.items()],
            key=lambda x: x[1], reverse=True
        )[:5]
        
        print("\n🔥 Catégories les plus populaires:")
        for cat, count in popular_categories:
            print(f"   • {cat}: {count} articles")


def main():
    """Fonction principale."""
    index_path = "arxiv_index.faiss"
    metadata_path = "arxiv_metadata.json"
    
    try:
        searcher = EnhancedArticleSearcher(index_path, metadata_path)
        searcher.interactive_search()
        
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        print("🔧 Vérifiez que les fichiers d'index et métadonnées existent.")

if __name__ == "__main__":
    main()