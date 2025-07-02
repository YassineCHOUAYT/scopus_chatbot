import pandas as pd
import sqlite3
import json
import re
from datetime import datetime
from config import DATABASE_PATH

class DataProcessor:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Initialisation de la base de données SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table articles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scopus_id TEXT UNIQUE,
                title TEXT,
                abstract TEXT,
                publication_date DATE,
                journal TEXT,
                doi TEXT,
                keywords TEXT,
                subject_areas TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table auteurs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS authors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auid TEXT UNIQUE,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table affiliations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS affiliations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                affiliation_id TEXT UNIQUE,
                name TEXT,
                country TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table relations article-auteur
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS article_authors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                author_id INTEGER,
                FOREIGN KEY (article_id) REFERENCES articles (id),
                FOREIGN KEY (author_id) REFERENCES authors (id)
            )
        ''')
        
        # Table relations auteur-affiliation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS author_affiliations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id INTEGER,
                affiliation_id INTEGER,
                FOREIGN KEY (author_id) REFERENCES authors (id),
                FOREIGN KEY (affiliation_id) REFERENCES affiliations (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def clean_text(self, text):
        """Nettoyage du texte"""
        if not text or pd.isna(text):
            return ""
        
        # Suppression des caractères spéciaux
        text = re.sub(r'[^\w\s\-.,;:!?()]', ' ', str(text))
        # Normalisation des espaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def parse_date(self, date_str):
        """Parsing des dates"""
        if not date_str or pd.isna(date_str):
            return None
        
        try:
            # Format YYYY-MM-DD
            return datetime.strptime(str(date_str)[:10], '%Y-%m-%d').date()
        except:
            try:
                # Format YYYY
                return datetime.strptime(str(date_str)[:4], '%Y').date()
            except:
                return None
    
    def process_articles(self, raw_data_file):
        """Traitement et insertion des articles"""
        with open(raw_data_file, 'r', encoding='utf-8') as f:
            articles_data = json.load(f)
        
        # Conversion en DataFrame pour nettoyage
        df = pd.DataFrame(articles_data)
        
        # Suppression des doublons
        df = df.drop_duplicates(subset=['scopus_id'], keep='first')
        
        # Nettoyage des données
        df['title'] = df['title'].apply(self.clean_text)
        df['abstract'] = df['abstract'].apply(self.clean_text)
        df['journal'] = df['journal'].apply(self.clean_text)
        df['publication_date'] = df['publication_date'].apply(self.parse_date)
        
        # Filtrage des articles sans résumé
        df = df[df['abstract'].str.len() > 50]
        
        conn = sqlite3.connect(self.db_path)
        
        processed_count = 0
        
        for _, row in df.iterrows():
            try:
                # Insertion article
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR IGNORE INTO articles 
                    (scopus_id, title, abstract, publication_date, journal, doi, keywords, subject_areas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['scopus_id'],
                    row['title'],
                    row['abstract'],
                    row['publication_date'],
                    row['journal'],
                    row['doi'],
                    row['keywords'],
                    row['subject_areas']
                ))
                
                article_id = cursor.lastrowid
                if article_id == 0:  # Article déjà existant
                    cursor.execute('SELECT id FROM articles WHERE scopus_id = ?', (row['scopus_id'],))
                    article_id = cursor.fetchone()[0]
                
                # Traitement des auteurs
                if isinstance(row['authors'], list):
                    for author_data in row['authors']:
                        if author_data.get('auid'):
                            # Insertion auteur
                            cursor.execute('''
                                INSERT OR IGNORE INTO authors (auid, name)
                                VALUES (?, ?)
                            ''', (author_data['auid'], author_data['name']))
                            
                            # Récupération ID auteur
                            cursor.execute('SELECT id FROM authors WHERE auid = ?', (author_data['auid'],))
                            author_id = cursor.fetchone()[0]
                            
                            # Liaison article-auteur
                            cursor.execute('''
                                INSERT OR IGNORE INTO article_authors (article_id, author_id)
                                VALUES (?, ?)
                            ''', (article_id, author_id))
                
                # Traitement des affiliations
                if isinstance(row['affiliations'], list):
                    for affil_data in row['affiliations']:
                        if affil_data.get('affiliation_id'):
                            # Insertion affiliation
                            cursor.execute('''
                                INSERT OR IGNORE INTO affiliations (affiliation_id, name, country)
                                VALUES (?, ?, ?)
                            ''', (affil_data['affiliation_id'], affil_data['name'], affil_data['country']))
                
                processed_count += 1
                if processed_count % 100 == 0:
                    print(f"Articles traités: {processed_count}")
                    conn.commit()
            
            except Exception as e:
                print(f"Erreur traitement article {row.get('scopus_id', 'N/A')}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"Traitement terminé: {processed_count} articles")
        return processed_count
    
    def get_articles_for_indexing(self):
        """Récupération des articles pour indexation sémantique"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT id, scopus_id, title, abstract, publication_date, journal
            FROM articles
            WHERE abstract IS NOT NULL AND LENGTH(abstract) > 50
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df

# Exemple d'utilisation
if __name__ == "__main__":
    processor = DataProcessor()
    
    # Traitement des données extraites
    count = processor.process_articles('scopus_raw_data.json')
    print(f"Articles traités et stockés: {count}")
    
    # Récupération pour indexation
    articles_df = processor.get_articles_for_indexing()
    print(f"Articles prêts pour indexation: {len(articles_df)}")