import requests
import pandas as pd
import json
import time
from config import SCOPUS_API_KEY, SCOPUS_BASE_URL

class ScopusExtractor:
    def __init__(self):
        self.api_key = SCOPUS_API_KEY
        self.base_url = SCOPUS_BASE_URL
        self.headers = {
            'X-ELS-APIKey': self.api_key,
            'Accept': 'application/json'
        }
    
    def search_articles(self, query, count=100, start=0):
        """Recherche d'articles via l'API Scopus"""
        params = {
            'query': query,
            'count': count,
            'start': start,
            'field': 'dc:identifier,dc:title,prism:publicationName,prism:coverDate,prism:doi,dc:description,authkeywords,subject-area,author,affiliation'
        }
        
        try:
            response = requests.get(self.base_url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur API: {e}")
            return None
    
    def extract_articles_data(self, search_results):
        """Extraction des données d'articles"""
        articles = []
        
        if not search_results or 'search-results' not in search_results:
            return articles
        
        entries = search_results['search-results'].get('entry', [])
        
        for entry in entries:
            article = {
                'scopus_id': entry.get('dc:identifier', '').replace('SCOPUS_ID:', ''),
                'title': entry.get('dc:title', ''),
                'abstract': entry.get('dc:description', ''),
                'publication_date': entry.get('prism:coverDate', ''),
                'journal': entry.get('prism:publicationName', ''),
                'doi': entry.get('prism:doi', ''),
                'keywords': entry.get('authkeywords', ''),
                'subject_areas': self._extract_subject_areas(entry.get('subject-area', [])),
                'authors': self._extract_authors(entry.get('author', [])),
                'affiliations': self._extract_affiliations(entry.get('affiliation', []))
            }
            articles.append(article)
        
        return articles
    
    def _extract_subject_areas(self, subject_areas):
        """Extraction des domaines de recherche"""
        if isinstance(subject_areas, list):
            return '; '.join([area.get('@abbrev', '') for area in subject_areas])
        return ''
    
    def _extract_authors(self, authors):
        """Extraction des auteurs"""
        if isinstance(authors, list):
            author_list = []
            for author in authors:
                author_info = {
                    'auid': author.get('@auid', ''),
                    'name': author.get('preferred-name', {}).get('ce:given-name', '') + ' ' + 
                           author.get('preferred-name', {}).get('ce:surname', ''),
                    'affiliation_id': author.get('@affiliation', '')
                }
                author_list.append(author_info)
            return author_list
        return []
    
    def _extract_affiliations(self, affiliations):
        """Extraction des affiliations"""
        if isinstance(affiliations, list):
            affil_list = []
            for affil in affiliations:
                affil_info = {
                    'affiliation_id': affil.get('@id', ''),
                    'name': affil.get('affilname', ''),
                    'country': affil.get('affiliation-country', '')
                }
                affil_list.append(affil_info)
            return affil_list
        return []
    
    def extract_multiple_queries(self, queries, max_results=1000):
        """Extraction de données pour plusieurs requêtes"""
        all_articles = []
        
        for query in queries:
            print(f"Extraction pour: {query}")
            start = 0
            count = 25  # Limite API Scopus
            
            while start < max_results:
                results = self.search_articles(query, count, start)
                if not results:
                    break
                
                articles = self.extract_articles_data(results)
                if not articles:
                    break
                
                all_articles.extend(articles)
                start += count
                time.sleep(1)  # Respect des limites API
                
                print(f"Articles extraits: {len(all_articles)}")
        
        return all_articles

# Exemple d'utilisation
if __name__ == "__main__":
    extractor = ScopusExtractor()
    
    # Requêtes d'exemple
    queries = [
        "artificial intelligence",
        "machine learning",
        "deep learning",
        "natural language processing"
    ]
    
    articles = extractor.extract_multiple_queries(queries, max_results=500)
    
    # Sauvegarde en JSON temporaire
    with open('scopus_raw_data.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    
    print(f"Total articles extraits: {len(articles)}")