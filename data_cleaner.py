import pandas as pd
import numpy as np
import re
import json
import logging
from datetime import datetime
from collections import Counter
import string
from typing import List, Dict, Any, Optional

from config import setup_logging
from database_manager import DatabaseManager

logger = setup_logging()

class DataCleaner:
    def __init__(self):
        self.stopwords = self._load_stopwords()
        
    def _load_stopwords(self):
        """Charge une liste de mots vides en anglais."""
        # Liste basique de mots vides
        return {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'we', 'can', 'have', 'this', 'they',
            'not', 'or', 'but', 'been', 'which', 'their', 'there', 'these',
            'more', 'than', 'such', 'also', 'other', 'one', 'two', 'our',
            'all', 'any', 'each', 'first', 'most', 'only', 'over', 'under',
            'where', 'when', 'why', 'how', 'what', 'who', 'would', 'could',
            'should', 'may', 'might', 'must', 'do', 'does', 'did', 'doing',
            'done', 'get', 'got', 'getting', 'give', 'given', 'go', 'going',
            'gone', 'had', 'having', 'into', 'like', 'make', 'making', 'made',
            'see', 'seen', 'take', 'taken', 'taking', 'took', 'use', 'used',
            'using', 'work', 'works', 'worked', 'working'
        }
    
    def clean_text(self, text: str) -> str:
        """Nettoie et normalise le texte."""
        if not text or pd.isna(text):
            return ""
        
        # Convertir en string si nécessaire
        text = str(text)
        
        # Supprimer les caractères de contrôle et les espaces multiples
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les espaces en début et fin
        text = text.strip()
        
        return text
    
    def clean_title(self, title: str) -> str:
        """Nettoie spécifiquement les titres."""
        if not title:
            return ""
        
        title = self.clean_text(title)
        
        # Supprimer les caractères spéciaux en début/fin
        title = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', title)
        
        return title
    
    def clean_abstract(self, abstract: str) -> str:
        """Nettoie spécifiquement les résumés."""
        if not abstract:
            return ""
        
        abstract = self.clean_text(abstract)
        
        # Supprimer les références LaTeX communes
        abstract = re.sub(r'\$[^$]*\$', '', abstract)  # Formules mathématiques
        abstract = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', abstract)  # Commandes LaTeX
        abstract = re.sub(r'\\[a-zA-Z]+', '', abstract)  # Commandes LaTeX simples
        
        # Nettoyer les espaces multiples
        abstract = re.sub(r'\s+', ' ', abstract).strip()
        
        return abstract
    
    def clean_author_name(self, name: str) -> str:
        """Nettoie et normalise les noms d'auteurs."""
        if not name:
            return ""
        
        name = self.clean_text(name)
        
        # Supprimer les caractères spéciaux
        name = re.sub(r'[^\w\s\-\.]', '', name)
        
        # Normaliser les espaces
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Capitaliser correctement
        name = name.title()
        
        return name
    
    def clean_affiliation(self, affiliation: str) -> str:
        """Nettoie les affiliations."""
        if not affiliation:
            return ""
        
        affiliation = self.clean_text(affiliation)
        
        # Supprimer les adresses email
        affiliation = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', affiliation)
        
        # Normaliser les espaces
        affiliation = re.sub(r'\s+', ' ', affiliation).strip()
        
        return affiliation
    
    def extract_keywords_from_text(self, text: str, min_length: int = 3, max_keywords: int = 20) -> List[str]:
        """Extrait les mots-clés d'un texte."""
        if not text:
            return []
        
        # Nettoyer le texte
        text = self.clean_text(text.lower())
        
        # Supprimer la ponctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Diviser en mots
        words = text.split()
        
        # Filtrer les mots
        filtered_words = [
            word for word in words 
            if len(word) >= min_length 
            and word not in self.stopwords
            and word.isalpha()
        ]
        
        # Compter les occurrences
        word_counts = Counter(filtered_words)
        
        # Retourner les mots les plus fréquents
        return [word for word, count in word_counts.most_common(max_keywords)]
    
    def normalize_category(self, category: str) -> str:
        """Normalise les catégories ArXiv."""
        if not category:
            return ""
        
        category = category.strip().lower()
        
        # Dictionnaire de normalisation des catégories
        category_mapping = {
            'cs.ai': 'cs.AI',
            'cs.cl': 'cs.CL', 
            'cs.cv': 'cs.CV',
            'cs.lg': 'cs.LG',
            'stat.ml': 'stat.ML',
            'math.st': 'math.ST',
            'q-bio.qm': 'q-bio.QM',
            'physics.data-an': 'physics.data-an'
        }
        
        return category_mapping.get(category, category)
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse une date au format ArXiv."""
        if not date_str:
            return None
        
        try:
            # Format ArXiv: YYYY-MM-DD
            if len(date_str) >= 10:
                return datetime.strptime(date_str[:10], '%Y-%m-%d')
            return None
        except ValueError:
            logger.warning(f"Impossible de parser la date: {date_str}")
            return None
    
    def detect_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """Détecte et supprime les doublons."""
        seen_ids = set()
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            # Vérifier l'ID ArXiv
            arxiv_id = article.get('arxiv_id', '')
            if arxiv_id in seen_ids:
                logger.info(f"Doublon détecté par ID: {arxiv_id}")
                continue
            
            # Vérifier le titre (normalisation)
            title = self.clean_title(article.get('title', ''))
            title_normalized = re.sub(r'[^\w\s]', '', title.lower())
            
            if title_normalized in seen_titles:
                logger.info(f"Doublon détecté par titre: {title}")
                continue
            
            seen_ids.add(arxiv_id)
            seen_titles.add(title_normalized)
            unique_articles.append(article)
        
        logger.info(f"Suppression de {len(articles) - len(unique_articles)} doublons")
        return unique_articles
    
    def validate_article(self, article: Dict) -> bool:
        """Valide qu'un article contient les informations minimales."""
        required_fields = ['arxiv_id', 'title', 'abstract']
        
        for field in required_fields:
            if not article.get(field):
                logger.warning(f"Article invalide - champ manquant: {field}")
                return False
        
        # Vérifier la longueur minimale
        if len(article['title']) < 10:
            logger.warning(f"Titre trop court: {article['title']}")
            return False
        
        if len(article['abstract']) < 50:
            logger.warning(f"Résumé trop court pour l'article: {article['arxiv_id']}")
            return False
        
        return True
    
    def extract_country_from_affiliation(self, affiliation: str) -> Optional[str]:
        """Extrait le pays d'une affiliation."""
        if not affiliation:
            return None
        
        # Liste des pays courants (format simple)
        countries = {
            'usa': 'United States',
            'united states': 'United States',
            'us': 'United States',
            'uk': 'United Kingdom',
            'united kingdom': 'United Kingdom',
            'england': 'United Kingdom',
            'france': 'France',
            'germany': 'Germany',
            'deutschland': 'Germany',
            'china': 'China',
            'japan': 'Japan',
            'canada': 'Canada',
            'australia': 'Australia',
            'italy': 'Italy',
            'spain': 'Spain',
            'netherlands': 'Netherlands',
            'sweden': 'Sweden',
            'switzerland': 'Switzerland',
            'india': 'India',
            'brazil': 'Brazil',
            'russia': 'Russia',
            'south korea': 'South Korea',
            'korea': 'South Korea',
            'israel': 'Israel',
            'singapore': 'Singapore',
            'taiwan': 'Taiwan',
            'belgium': 'Belgium',
            'denmark': 'Denmark',
            'norway': 'Norway',
            'finland': 'Finland',
            'austria': 'Austria',
            'poland': 'Poland',
            'czechia': 'Czech Republic',
            'czech republic': 'Czech Republic'
        }
        
        affiliation_lower = affiliation.lower()
        
        # Chercher les pays dans l'affiliation
        for key, country in countries.items():
            if key in affiliation_lower:
                return country
        
        return None
    
    def clean_articles_data(self, articles: List[Dict]) -> List[Dict]:
        """Nettoie une liste d'articles."""
        logger.info(f"Nettoyage de {len(articles)} articles")
        
        cleaned_articles = []
        
        for article in articles:
            try:
                # Nettoyer les champs texte
                article['title'] = self.clean_title(article.get('title', ''))
                article['abstract'] = self.clean_abstract(article.get('abstract', ''))
                
                # Nettoyer les catégories
                if 'categories' in article and article['categories']:
                    if isinstance(article['categories'], list):
                        article['categories'] = [self.normalize_category(cat) for cat in article['categories']]
                    else:
                        article['categories'] = [self.normalize_category(cat.strip()) for cat in article['categories'].split(',')]
                
                # Normaliser la catégorie principale
                if 'primary_category' in article:
                    article['primary_category'] = self.normalize_category(article['primary_category'])
                
                # Nettoyer les auteurs
                if 'authors' in article and article['authors']:
                    for author in article['authors']:
                        author['name'] = self.clean_author_name(author.get('name', ''))
                        author['affiliation'] = self.clean_affiliation(author.get('affiliation', ''))
                        
                        # Extraire le pays de l'affiliation
                        if author['affiliation']:
                            author['country'] = self.extract_country_from_affiliation(author['affiliation'])
                
                # Parser les dates
                if 'published_date' in article:
                    parsed_date = self.parse_date(article['published_date'])
                    if parsed_date:
                        article['published_year'] = parsed_date.year
                        article['published_month'] = parsed_date.month
                
                # Extraire les mots-clés du titre et de l'abstract
                title_keywords = self.extract_keywords_from_text(article['title'], max_keywords=10)
                abstract_keywords = self.extract_keywords_from_text(article['abstract'], max_keywords=15)
                article['extracted_keywords'] = list(set(title_keywords + abstract_keywords))
                
                # Valider l'article
                if self.validate_article(article):
                    cleaned_articles.append(article)
                else:
                    logger.warning(f"Article invalide ignoré: {article.get('arxiv_id', 'ID_MANQUANT')}")
                    
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage de l'article {article.get('arxiv_id', 'ID_MANQUANT')}: {e}")
                continue
        
        # Supprimer les doublons
        cleaned_articles = self.detect_duplicates(cleaned_articles)
        
        logger.info(f"Nettoyage terminé. {len(cleaned_articles)} articles valides")
        return cleaned_articles
    
    def clean_database_articles(self):
        """Nettoie les articles directement dans la base de données."""
        logger.info("Nettoyage des articles dans la base de données")
        
        try:
            with DatabaseManager() as db:
                # Récupérer tous les articles
                db.cursor.execute("SELECT * FROM articles")
                articles = db.cursor.fetchall()
                
                logger.info(f"Nettoyage de {len(articles)} articles en base")
                
                for article in articles:
                    # Convertir en dictionnaire
                    article_dict = {
                        'id': article[0],
                        'arxiv_id': article[1],
                        'title': article[2],
                        'abstract': article[3],
                        'published_date': article[4],
                        'categories': article[6],
                        'primary_category': article[7]
                    }
                    
                    # Nettoyer les données
                    cleaned_title = self.clean_title(article_dict['title'])
                    cleaned_abstract = self.clean_abstract(article_dict['abstract'])
                    
                    # Mettre à jour en base
                    update_query = """
                    UPDATE articles 
                    SET title = %s, abstract = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """
                    
                    db.cursor.execute(update_query, (cleaned_title, cleaned_abstract, article_dict['id']))
                
                db.connection.commit()
                logger.info("Nettoyage en base terminé")
                
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage en base: {e}")
    
    def generate_cleaning_report(self, original_articles: List[Dict], cleaned_articles: List[Dict]) -> Dict:
        """Génère un rapport de nettoyage."""
        report = {
            'original_count': len(original_articles),
            'cleaned_count': len(cleaned_articles),
            'removed_count': len(original_articles) - len(cleaned_articles),
            'removal_rate': (len(original_articles) - len(cleaned_articles)) / len(original_articles) * 100 if original_articles else 0,
            'cleaning_timestamp': datetime.now().isoformat()
        }
        
        # Statistiques par catégorie
        if cleaned_articles:
            categories = [article.get('primary_category') for article in cleaned_articles if article.get('primary_category')]
            report['categories_distribution'] = dict(Counter(categories))
            
            # Statistiques par année
            years = [article.get('published_year') for article in cleaned_articles if article.get('published_year')]
            report['years_distribution'] = dict(Counter(years))
        
        return report


def main():
    """Fonction principale pour tester le nettoyeur."""
    cleaner = DataCleaner()
    
    # Test avec des données d'exemple
    test_articles = [
        {
            'arxiv_id': '2023.12345',
            'title': 'Machine Learning in Healthcare  ',
            'abstract': 'This paper presents a novel approach to machine learning in healthcare...',
            'published_date': '2023-12-01',
            'categories': ['cs.LG', 'cs.AI'],
            'primary_category': 'cs.lg',
            'authors': [
                {'name': 'john doe', 'affiliation': 'MIT, Cambridge, MA, USA'},
                {'name': 'jane smith', 'affiliation': 'Stanford University, USA'}
            ]
        },
        {
            'arxiv_id': '2023.67890',
            'title': 'Deep Learning for Computer Vision',
            'abstract': 'We propose a new deep learning architecture for computer vision tasks...',
            'published_date': '2023-11-15',
            'categories': ['cs.CV', 'cs.LG'],
            'primary_category': 'cs.cv',
            'authors': [
                {'name': 'alice johnson', 'affiliation': 'Google Research, Mountain View, CA, USA'}
            ]
        }
    ]
    
    print("=== Test du nettoyeur de données ===")
    print(f"Articles originaux: {len(test_articles)}")
    
    # Nettoyer les articles
    cleaned = cleaner.clean_articles_data(test_articles)
    print(f"Articles nettoyés: {len(cleaned)}")
    
    # Générer un rapport
    report = cleaner.generate_cleaning_report(test_articles, cleaned)
    print(f"Rapport de nettoyage: {report}")
    
    # Afficher un exemple d'article nettoyé
    if cleaned:
        print("\nExemple d'article nettoyé:")
        print(json.dumps(cleaned[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()