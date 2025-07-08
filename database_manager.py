import mysql.connector
from mysql.connector import Error
import logging
from config import DB_CONFIG, setup_logging

logger = setup_logging()

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Établit la connexion à la base de données MySQL."""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor()
            logger.info("Connexion à MySQL établie avec succès")
            return True
        except Error as e:
            logger.error(f"Erreur lors de la connexion à MySQL: {e}")
            return False
    
    def disconnect(self):
        """Ferme la connexion à la base de données."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Connexion fermée")
    
    def create_database(self):
        """Crée la base de données si elle n'existe pas."""
        try:
            # Connexion sans spécifier la base de données
            temp_config = DB_CONFIG.copy()
            temp_config.pop('database', None)
            temp_connection = mysql.connector.connect(**temp_config)
            temp_cursor = temp_connection.cursor()
            
            temp_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            temp_cursor.close()
            temp_connection.close()
            
            logger.info(f"Base de données {DB_CONFIG['database']} créée ou existe déjà")
            return True
        except Error as e:
            logger.error(f"Erreur lors de la création de la base de données: {e}")
            return False
    
    def create_tables(self):
        """Crée les tables nécessaires pour le projet."""
        
        # Table articles
        articles_table = """
        CREATE TABLE IF NOT EXISTS articles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            arxiv_id VARCHAR(50) UNIQUE NOT NULL,
            title TEXT NOT NULL,
            abstract TEXT,
            published_date DATE,
            updated_date DATE,
            categories TEXT,
            primary_category VARCHAR(50),
            doi VARCHAR(255),
            journal_reference TEXT,
            comments TEXT,
            pdf_link VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_arxiv_id (arxiv_id),
            INDEX idx_published_date (published_date),
            INDEX idx_primary_category (primary_category)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # Table authors
        authors_table = """
        CREATE TABLE IF NOT EXISTS authors (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            affiliation TEXT,
            email VARCHAR(255),
            orcid VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_name (name),
            INDEX idx_orcid (orcid)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # Table affiliations
        affiliations_table = """
        CREATE TABLE IF NOT EXISTS affiliations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            institution_name VARCHAR(500) NOT NULL,
            country VARCHAR(100),
            city VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_institution (institution_name),
            INDEX idx_country (country)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # Table article_authors (relation many-to-many)
        article_authors_table = """
        CREATE TABLE IF NOT EXISTS article_authors (
            id INT AUTO_INCREMENT PRIMARY KEY,
            article_id INT NOT NULL,
            author_id INT NOT NULL,
            affiliation_id INT,
            author_position INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
            FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE,
            FOREIGN KEY (affiliation_id) REFERENCES affiliations(id) ON DELETE SET NULL,
            UNIQUE KEY unique_article_author (article_id, author_id),
            INDEX idx_article_id (article_id),
            INDEX idx_author_id (author_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # Table keywords
        keywords_table = """
        CREATE TABLE IF NOT EXISTS keywords (
            id INT AUTO_INCREMENT PRIMARY KEY,
            keyword VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_keyword (keyword)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # Table article_keywords (relation many-to-many)
        article_keywords_table = """
        CREATE TABLE IF NOT EXISTS article_keywords (
            id INT AUTO_INCREMENT PRIMARY KEY,
            article_id INT NOT NULL,
            keyword_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
            FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE,
            UNIQUE KEY unique_article_keyword (article_id, keyword_id),
            INDEX idx_article_id (article_id),
            INDEX idx_keyword_id (keyword_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # Table extraction_logs
        extraction_logs_table = """
        CREATE TABLE IF NOT EXISTS extraction_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            query_terms TEXT,
            start_date DATE,
            end_date DATE,
            total_results INT,
            extracted_count INT,
            status ENUM('running', 'completed', 'error', 'cancelled'),
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP NULL,
            INDEX idx_status (status),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        tables = [
            articles_table,
            authors_table,
            affiliations_table,
            article_authors_table,
            keywords_table,
            article_keywords_table,
            extraction_logs_table
        ]
        
        try:
            for table in tables:
                self.cursor.execute(table)
            self.connection.commit()
            logger.info("Toutes les tables ont été créées avec succès")
            return True
        except Error as e:
            logger.error(f"Erreur lors de la création des tables: {e}")
            self.connection.rollback()
            return False
    
    def insert_article(self, article_data):
        """Insère un article dans la base de données."""
        insert_query = """
        INSERT INTO articles (arxiv_id, title, abstract, published_date, updated_date, 
                            categories, primary_category, doi, journal_reference, comments, pdf_link)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            abstract = VALUES(abstract),
            updated_date = VALUES(updated_date),
            categories = VALUES(categories),
            primary_category = VALUES(primary_category),
            doi = VALUES(doi),
            journal_reference = VALUES(journal_reference),
            comments = VALUES(comments),
            pdf_link = VALUES(pdf_link)
        """
        
        try:
            self.cursor.execute(insert_query, article_data)
            self.connection.commit()
            return self.cursor.lastrowid
        except Error as e:
            logger.error(f"Erreur lors de l'insertion de l'article: {e}")
            self.connection.rollback()
            return None
    
    def insert_author(self, author_data):
        """Insère un auteur dans la base de données."""
        insert_query = """
        INSERT INTO authors (name, affiliation, email, orcid)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            affiliation = VALUES(affiliation),
            email = VALUES(email),
            orcid = VALUES(orcid)
        """
        
        try:
            self.cursor.execute(insert_query, author_data)
            self.connection.commit()
            return self.cursor.lastrowid
        except Error as e:
            logger.error(f"Erreur lors de l'insertion de l'auteur: {e}")
            self.connection.rollback()
            return None
    
    def get_article_by_arxiv_id(self, arxiv_id):
        """Récupère un article par son ID ArXiv."""
        query = "SELECT * FROM articles WHERE arxiv_id = %s"
        try:
            self.cursor.execute(query, (arxiv_id,))
            return self.cursor.fetchone()
        except Error as e:
            logger.error(f"Erreur lors de la récupération de l'article: {e}")
            return None
    
    def get_statistics(self):
        """Récupère des statistiques sur la base de données."""
        try:
            stats = {}
            
            # Nombre total d'articles
            self.cursor.execute("SELECT COUNT(*) FROM articles")
            stats['total_articles'] = self.cursor.fetchone()[0]
            
            # Nombre total d'auteurs
            self.cursor.execute("SELECT COUNT(*) FROM authors")
            stats['total_authors'] = self.cursor.fetchone()[0]
            
            # Articles par catégorie
            self.cursor.execute("""
                SELECT primary_category, COUNT(*) as count 
                FROM articles 
                GROUP BY primary_category 
                ORDER BY count DESC
            """)
            stats['articles_by_category'] = self.cursor.fetchall()
            
            # Articles par année
            self.cursor.execute("""
                SELECT YEAR(published_date) as year, COUNT(*) as count 
                FROM articles 
                WHERE published_date IS NOT NULL
                GROUP BY YEAR(published_date) 
                ORDER BY year DESC
            """)
            stats['articles_by_year'] = self.cursor.fetchall()
            
            return stats
        except Error as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

# Fonction utilitaire pour initialiser la base de données
def initialize_database():
    """Initialise la base de données avec toutes les tables nécessaires."""
    db_manager = DatabaseManager()
    
    # Créer la base de données
    if not db_manager.create_database():
        return False
    
    # Se connecter et créer les tables
    if db_manager.connect():
        success = db_manager.create_tables()
        db_manager.disconnect()
        return success
    
    return False

if __name__ == "__main__":
    # Test de la configuration
    print("Initialisation de la base de données...")
    if initialize_database():
        print("Base de données initialisée avec succès!")
        
        # Test des statistiques
        with DatabaseManager() as db:
            stats = db.get_statistics()
            if stats:
                print(f"Statistiques:")
                print(f"- Articles: {stats['total_articles']}")
                print(f"- Auteurs: {stats['total_authors']}")
    else:
        print("Erreur lors de l'initialisation de la base de données.")