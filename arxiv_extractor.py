import requests
import xml.etree.ElementTree as ET
import time
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode
import pandas as pd
import os
from tqdm import tqdm
import json

from config import ARXIV_CONFIG, PROJECT_CONFIG, setup_logging
from database_manager import DatabaseManager

logger = setup_logging()

class ArxivExtractor:
    def __init__(self):
        self.base_url = ARXIV_CONFIG['base_url']
        self.max_results = ARXIV_CONFIG['max_results']
        self.delay = ARXIV_CONFIG['delay']
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ArxivExtractor/1.0 (mailto:your-email@example.com)'
        })
        
    def build_query(self, search_terms=None, categories=None, authors=None, 
                   start_date=None, end_date=None):
        """Construit une requête pour l'API ArXiv."""
        query_parts = []
        
        # Termes de recherche dans le titre ou l'abstract
        if search_terms:
            if isinstance(search_terms, list):
                search_terms = ' AND '.join(search_terms)
            query_parts.append(f'(ti:"{search_terms}" OR abs:"{search_terms}")')
        
        # Catégories
        if categories:
            if isinstance(categories, list):
                cat_query = ' OR '.join([f'cat:{cat}' for cat in categories])
                query_parts.append(f'({cat_query})')
            else:
                query_parts.append(f'cat:{categories}')
        
        # Auteurs
        if authors:
            if isinstance(authors, list):
                auth_query = ' OR '.join([f'au:"{author}"' for author in authors])
                query_parts.append(f'({auth_query})')
            else:
                query_parts.append(f'au:"{authors}"')
        
        # Dates
        if start_date or end_date:
            if start_date and end_date:
                query_parts.append(f'submittedDate:[{start_date} TO {end_date}]')
            elif start_date:
                query_parts.append(f'submittedDate:[{start_date} TO *]')
            elif end_date:
                query_parts.append(f'submittedDate:[* TO {end_date}]')
        
        return ' AND '.join(query_parts) if query_parts else 'all'
    
    def extract_article_data(self, entry):
        """Extrait les données d'un article depuis l'XML ArXiv."""
        try:
            # Namespaces utilisés par ArXiv
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            # Données de base
            article_data = {
                'arxiv_id': entry.find('atom:id', namespaces).text.split('/')[-1],
                'title': entry.find('atom:title', namespaces).text.strip(),
                'abstract': entry.find('atom:summary', namespaces).text.strip(),
                'published_date': entry.find('atom:published', namespaces).text[:10],
                'updated_date': entry.find('atom:updated', namespaces).text[:10],
                'pdf_link': None,
                'doi': None,
                'journal_reference': None,
                'comments': None,
                'categories': [],
                'primary_category': None,
                'authors': []
            }
            
            # Liens (PDF)
            for link in entry.findall('atom:link', namespaces):
                if link.get('type') == 'application/pdf':
                    article_data['pdf_link'] = link.get('href')
                    break
            
            # Informations ArXiv spécifiques
            primary_cat = entry.find('arxiv:primary_category', namespaces)
            if primary_cat is not None:
                article_data['primary_category'] = primary_cat.get('term')
            
            # Toutes les catégories
            for category in entry.findall('atom:category', namespaces):
                article_data['categories'].append(category.get('term'))
            
            # DOI
            doi_elem = entry.find('arxiv:doi', namespaces)
            if doi_elem is not None:
                article_data['doi'] = doi_elem.text
            
            # Journal reference
            journal_elem = entry.find('arxiv:journal_ref', namespaces)
            if journal_elem is not None:
                article_data['journal_reference'] = journal_elem.text
            
            # Commentaires
            comment_elem = entry.find('arxiv:comment', namespaces)
            if comment_elem is not None:
                article_data['comments'] = comment_elem.text
            
            # Auteurs
            for author in entry.findall('atom:author', namespaces):
                name_elem = author.find('atom:name', namespaces)
                if name_elem is not None:
                    affiliation_elem = author.find('arxiv:affiliation', namespaces)
                    author_data = {
                        'name': name_elem.text,
                        'affiliation': affiliation_elem.text if affiliation_elem is not None else None
                    }
                    article_data['authors'].append(author_data)
            
            return article_data
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des données de l'article: {e}")
            return None
    
    def search_articles(self, query, start=0, max_results=None):
        """Effectue une recherche sur ArXiv."""
        if max_results is None:
            max_results = self.max_results
        
        params = {
            'search_query': query,
            'start': start,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        url = f"{self.base_url}?{urlencode(params)}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parser la réponse XML
            root = ET.fromstring(response.content)
            
            # Extraire les informations de base
            total_results = int(root.find('{http://a9.com/-/spec/opensearch/1.1/}totalResults').text)
            start_index = int(root.find('{http://a9.com/-/spec/opensearch/1.1/}startIndex').text)
            items_per_page = int(root.find('{http://a9.com/-/spec/opensearch/1.1/}itemsPerPage').text)
            
            # Extraire les articles
            articles = []
            entries = root.findall('{http://www.w3.org/2005/Atom}entry')
            
            for entry in entries:
                article_data = self.extract_article_data(entry)
                if article_data:
                    articles.append(article_data)
            
            return {
                'total_results': total_results,
                'start_index': start_index,
                'items_per_page': items_per_page,
                'articles': articles
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la requête ArXiv: {e}")
            return None
        except ET.ParseError as e:
            logger.error(f"Erreur lors du parsing XML: {e}")
            return None
    
    def extract_all_articles(self, query, max_total_results=1000, 
                           save_to_db=True, save_to_file=True):
        """Extrait tous les articles correspondant à une requête."""
        logger.info(f"Début de l'extraction pour la requête: {query}")
        
        all_articles = []
        start = 0
        extracted_count = 0
        
        # Première requête pour connaître le nombre total
        initial_result = self.search_articles(query, start=0, max_results=1)
        if not initial_result:
            logger.error("Impossible d'effectuer la requête initiale")
            return []
        
        total_available = min(initial_result['total_results'], max_total_results)
        logger.info(f"Nombre total d'articles disponibles: {total_available}")
        
        # Barre de progression
        with tqdm(total=total_available, desc="Extraction des articles") as pbar:
            while extracted_count < total_available:
                # Calculer le nombre d'articles à récupérer
                remaining = total_available - extracted_count
                batch_size = min(self.max_results, remaining)
                
                # Effectuer la requête
                result = self.search_articles(query, start=start, max_results=batch_size)
                
                if not result or not result['articles']:
                    logger.warning(f"Aucun résultat pour start={start}")
                    break
                
                # Ajouter les articles
                batch_articles = result['articles']
                all_articles.extend(batch_articles)
                
                # Sauvegarder en base de données si demandé
                if save_to_db:
                    self.save_to_database(batch_articles)
                
                extracted_count += len(batch_articles)
                pbar.update(len(batch_articles))
                
                # Préparer la prochaine requête
                start += batch_size
                
                # Délai pour respecter les limites de l'API
                if extracted_count < total_available:
                    time.sleep(self.delay)
        
        logger.info(f"Extraction terminée. {len(all_articles)} articles extraits.")
        
        # Sauvegarder dans un fichier si demandé
        if save_to_file:
            self.save_to_file(all_articles, query)
        
        return all_articles
    
    def save_to_database(self, articles):
        """Sauvegarde les articles dans la base de données."""
        try:
            with DatabaseManager() as db:
                for article in articles:
                    # Préparer les données de l'article
                    article_data = (
                        article['arxiv_id'],
                        article['title'],
                        article['abstract'],
                        article['published_date'],
                        article['updated_date'],
                        ','.join(article['categories']),
                        article['primary_category'],
                        article['doi'],
                        article['journal_reference'],
                        article['comments'],
                        article['pdf_link']
                    )
                    
                    # Insérer l'article
                    article_id = db.insert_article(article_data)
                    
                    if article_id:
                        # Insérer les auteurs
                        for i, author in enumerate(article['authors']):
                            author_data = (
                                author['name'],
                                author['affiliation'],
                                None,  # email
                                None   # orcid
                            )
                            author_id = db.insert_author(author_data)
                            
                            if author_id:
                                # Lier l'article et l'auteur
                                link_query = """
                                INSERT INTO article_authors (article_id, author_id, author_position)
                                VALUES (%s, %s, %s)
                                ON DUPLICATE KEY UPDATE author_position = VALUES(author_position)
                                """
                                db.cursor.execute(link_query, (article_id, author_id, i + 1))
                        
                        db.connection.commit()
                        
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde en base de données: {e}")
    
    def save_to_file(self, articles, query):
        """Sauvegarde les articles dans des fichiers JSON et CSV."""
        try:
            # Créer le répertoire de données s'il n'existe pas
            os.makedirs(PROJECT_CONFIG['data_dir'], exist_ok=True)
            
            # Nom de fichier basé sur la requête et la date
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            clean_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename_base = f"{clean_query}_{timestamp}".replace(' ', '_')
            
            # Sauvegarder en JSON
            json_path = os.path.join(PROJECT_CONFIG['data_dir'], f"{filename_base}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
            
            # Préparer les données pour CSV
            csv_data = []
            for article in articles:
                csv_row = {
                    'arxiv_id': article['arxiv_id'],
                    'title': article['title'],
                    'abstract': article['abstract'][:500] + '...' if len(article['abstract']) > 500 else article['abstract'],
                    'published_date': article['published_date'],
                    'updated_date': article['updated_date'],
                    'primary_category': article['primary_category'],
                    'categories': ','.join(article['categories']),
                    'authors': '; '.join([author['name'] for author in article['authors']]),
                    'doi': article['doi'],
                    'journal_reference': article['journal_reference'],
                    'pdf_link': article['pdf_link']
                }
                csv_data.append(csv_row)
            
            # Sauvegarder en CSV
            csv_path = os.path.join(PROJECT_CONFIG['data_dir'], f"{filename_base}.csv")
            df = pd.DataFrame(csv_data)
            df.to_csv(csv_path, index=False, encoding='utf-8')
            
            logger.info(f"Données sauvegardées dans {json_path} et {csv_path}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des fichiers: {e}")
    
    def search_by_keywords(self, keywords, categories=None, start_date=None, end_date=None, max_results=1000):
        """Recherche par mots-clés avec filtres optionnels."""
        query = self.build_query(
            search_terms=keywords,
            categories=categories,
            start_date=start_date,
            end_date=end_date
        )
        
        return self.extract_all_articles(query, max_total_results=max_results)
    
    def search_by_author(self, author_name, max_results=1000):
        """Recherche par auteur."""
        query = self.build_query(authors=author_name)
        return self.extract_all_articles(query, max_total_results=max_results)
    
    def search_by_category(self, category, max_results=1000):
        """Recherche par catégorie."""
        query = self.build_query(categories=category)
        return self.extract_all_articles(query, max_total_results=max_results)
    
    def search_recent_articles(self, days_back=30, categories=None, max_results=1000):
        """Recherche les articles récents."""
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
        
        query = self.build_query(
            categories=categories,
            start_date=start_date,
            end_date=end_date
        )
        
        return self.extract_all_articles(query, max_total_results=max_results)


def main():
    """Fonction principale pour tester l'extracteur."""
    extractor = ArxivExtractor()
    
    # Exemple d'utilisation
    print("=== Test de l'extracteur ArXiv ===")
    
    # Recherche par mots-clés
    print("\n1. Recherche par mots-clés (machine learning)...")
    articles = extractor.search_by_keywords(
        keywords=["machine learning"],
        categories=["cs.LG", "cs.AI"],
        max_results=10
    )
    print(f"Nombre d'articles trouvés: {len(articles)}")
    
    # Recherche par catégorie
    print("\n2. Recherche par catégorie (Computer Vision)...")
    articles = extractor.search_by_category(
        category="cs.CV",
        max_results=10
    )
    print(f"Nombre d'articles trouvés: {len(articles)}")
    
    # Recherche d'articles récents
    print("\n3. Recherche d'articles récents (7 derniers jours)...")
    articles = extractor.search_recent_articles(
        days_back=7,
        categories=["cs.AI"],
        max_results=10
    )
    print(f"Nombre d'articles trouvés: {len(articles)}")


if __name__ == "__main__":
    main()