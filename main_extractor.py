#!/usr/bin/env python3
"""
Script principal pour l'extraction et le traitement des données ArXiv.
"""

import argparse
import logging
import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from config import setup_logging, ARXIV_CATEGORIES, PROJECT_CONFIG
from database_manager import DatabaseManager, initialize_database
from arxiv_extractor import ArxivExtractor
from data_cleaner import DataCleaner

logger = setup_logging()

class ArxivExtractionPipeline:
    """Pipeline complet d'extraction et de traitement des données ArXiv."""
    
    def __init__(self):
        self.extractor = ArxivExtractor()
        self.cleaner = DataCleaner()
        self.db_manager = DatabaseManager()
        
    def extract_by_keywords(self, keywords: List[str], categories: Optional[List[str]] = None,
                           start_date: Optional[str] = None, end_date: Optional[str] = None,
                           max_results: int = 1000) -> List[Dict]:
        logger.info(f"Extraction par mots-clés: {keywords}")
        articles = self.extractor.search_by_keywords(
            keywords=keywords,
            categories=categories,
            start_date=start_date,
            end_date=end_date,
            max_results=max_results
        )
        return self.cleaner.clean_articles_data(articles)
    
    def extract_by_category(self, category: str, max_results: int = 1000) -> List[Dict]:
        logger.info(f"Extraction par catégorie: {category}")
        articles = self.extractor.search_by_category(
            category=category,
            max_results=max_results
        )
        return self.cleaner.clean_articles_data(articles)
    
    def extract_by_author(self, author_name: str, max_results: int = 1000) -> List[Dict]:
        logger.info(f"Extraction par auteur: {author_name}")
        articles = self.extractor.search_by_author(
            author_name=author_name,
            max_results=max_results
        )
        return self.cleaner.clean_articles_data(articles)
    
    def extract_recent_articles(self, days_back: int = 30, categories: Optional[List[str]] = None,
                               max_results: int = 1000) -> List[Dict]:
        logger.info(f"Extraction des articles des {days_back} derniers jours")
        articles = self.extractor.search_recent_articles(
            days_back=days_back,
            categories=categories,
            max_results=max_results
        )
        return self.cleaner.clean_articles_data(articles)
    
    def run_extraction_job(self, job_config: Dict) -> Dict:
        job_type = job_config.get('type')
        results = {
            'job_config': job_config,
            'start_time': datetime.now().isoformat(),
            'articles': [],
            'success': False,
            'error': None
        }
        
        try:
            if job_type == 'keywords':
                articles = self.extract_by_keywords(
                    keywords=job_config['keywords'],
                    categories=job_config.get('categories'),
                    start_date=job_config.get('start_date'),
                    end_date=job_config.get('end_date'),
                    max_results=job_config.get('max_results', 1000)
                )
            elif job_type == 'category':
                articles = self.extract_by_category(
                    category=job_config['category'],
                    max_results=job_config.get('max_results', 1000)
                )
            elif job_type == 'author':
                articles = self.extract_by_author(
                    author_name=job_config['author'],
                    max_results=job_config.get('max_results', 1000)
                )
            elif job_type == 'recent':
                articles = self.extract_recent_articles(
                    days_back=job_config.get('days_back', 30),
                    categories=job_config.get('categories'),
                    max_results=job_config.get('max_results', 1000)
                )
            else:
                raise ValueError(f"Type de job non supporté: {job_type}")
            
            results['articles'] = articles
            results['success'] = True
            results['total_articles'] = len(articles)
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du job: {e}")
            results['error'] = str(e)
        
        results['end_time'] = datetime.now().isoformat()
        results['duration'] = (
            datetime.fromisoformat(results['end_time']) - 
            datetime.fromisoformat(results['start_time'])
        ).total_seconds()
        
        return results
    
    def save_extraction_results(self, results: Dict, output_dir: Optional[str] = None):
        if output_dir is None:
            output_dir = PROJECT_CONFIG['data_dir']
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"extraction_results_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Résultats sauvegardés dans {filepath}")
        return filepath

    def get_database_statistics(self) -> Dict:
        """Récupère les statistiques de la base de données."""
        try:
            with DatabaseManager() as db:
                stats = db.get_statistics()
                if stats:
                    logger.info(f"Statistiques de la base : {stats}")
                return stats
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques : {e}")
            return {}

def main():
    parser = argparse.ArgumentParser(description="Extraction et traitement des données ArXiv")
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")

    parser_keywords = subparsers.add_parser("extract_keywords", help="Extraction par mots-clés")
    parser_keywords.add_argument("--keywords", nargs="+", required=True, help="Liste de mots-clés")
    parser_keywords.add_argument("--categories", nargs="*", help="Catégories ArXiv (ex: cs.LG cs.AI)")
    parser_keywords.add_argument("--max-results", type=int, default=100, help="Nombre max d'articles")

    parser_category = subparsers.add_parser("extract_category", help="Extraction par catégorie")
    parser_category.add_argument("--category", required=True, help="Catégorie ArXiv (ex: cs.LG)")
    parser_category.add_argument("--max-results", type=int, default=100, help="Nombre max d'articles")

    parser_author = subparsers.add_parser("extract_author", help="Extraction par auteur")
    parser_author.add_argument("--author", required=True, help="Nom de l'auteur")
    parser_author.add_argument("--max-results", type=int, default=100, help="Nombre max d'articles")

    parser_recent = subparsers.add_parser("extract_recent", help="Extraction des articles récents")
    parser_recent.add_argument("--days-back", type=int, default=30, help="Nombre de jours en arrière")
    parser_recent.add_argument("--categories", nargs="*", help="Catégories ArXiv")
    parser_recent.add_argument("--max-results", type=int, default=100, help="Nombre max d'articles")

    parser_stats = subparsers.add_parser("stats", help="Afficher les statistiques de la base de données")

    parser_initdb = subparsers.add_parser("initdb", help="Initialiser la base de données")

    args = parser.parse_args()
    pipeline = ArxivExtractionPipeline()

    if args.command == "extract_keywords":
        articles = pipeline.extract_by_keywords(
            keywords=args.keywords,
            categories=args.categories,
            max_results=args.max_results
        )
        results = {
            "type": "keywords",
            "keywords": args.keywords,
            "categories": args.categories,
            "total_articles": len(articles),
            "articles": articles
        }
        pipeline.save_extraction_results(results)
        print(f"{len(articles)} articles extraits et sauvegardés.")

    elif args.command == "extract_category":
        articles = pipeline.extract_by_category(
            category=args.category,
            max_results=args.max_results
        )
        results = {
            "type": "category",
            "category": args.category,
            "total_articles": len(articles),
            "articles": articles
        }
        pipeline.save_extraction_results(results)
        print(f"{len(articles)} articles extraits et sauvegardés.")

    elif args.command == "extract_author":
        articles = pipeline.extract_by_author(
            author_name=args.author,
            max_results=args.max_results
        )
        results = {
            "type": "author",
            "author": args.author,
            "total_articles": len(articles),
            "articles": articles
        }
        pipeline.save_extraction_results(results)
        print(f"{len(articles)} articles extraits et sauvegardés.")

    elif args.command == "extract_recent":
        articles = pipeline.extract_recent_articles(
            days_back=args.days_back,
            categories=args.categories,
            max_results=args.max_results
        )
        results = {
            "type": "recent",
            "days_back": args.days_back,
            "categories": args.categories,
            "total_articles": len(articles),
            "articles": articles
        }
        pipeline.save_extraction_results(results)
        print(f"{len(articles)} articles extraits et sauvegardés.")

    elif args.command == "stats":
        stats = pipeline.get_database_statistics()
        print(json.dumps(stats, indent=2, ensure_ascii=False))

    elif args.command == "initdb":
        if initialize_database():
            print("Base de données initialisée avec succès.")
        else:
            print("Erreur lors de l'initialisation de la base de données.")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
