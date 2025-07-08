# database/init_db.py

import mysql.connector
from config import get_connection

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Table articles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id VARCHAR(100) PRIMARY KEY,
            title TEXT,
            authors TEXT,
            published DATETIME,
            updated DATETIME,
            link TEXT,
            abstract TEXT,
            primary_category VARCHAR(100),
            category TEXT,
            doi VARCHAR(100),
            journal_ref TEXT
        );
    """)    
     # Table article_embeddings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS article_embeddings (
    article_id VARCHAR(100) PRIMARY KEY,
    embedding BLOB,
    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
       );
    """)
    # Table authors
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS authors (
            id INT AUTO_INCREMENT PRIMARY KEY,
            scopus_author_id VARCHAR(30) UNIQUE,
            full_name VARCHAR(255),
            orcid VARCHAR(50),
            affiliation TEXT
        );
    """)

    # Table relation article–auteur
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS article_authors (
            article_id VARCHAR(100),
            author_id INT,
            PRIMARY KEY (article_id, author_id),
            FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
            FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    print("✅ Tables créées ou déjà existantes.")
    cursor.close()
    conn.close()


if __name__ == "__main__":
    create_tables()
