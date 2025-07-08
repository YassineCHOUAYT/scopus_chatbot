import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration base de données MySQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'arxiv_db'),
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': True
}

# Configuration ArXiv
ARXIV_CONFIG = {
    'base_url': os.getenv('ARXIV_BASE_URL', 'http://export.arxiv.org/api/query'),
    'max_results': int(os.getenv('MAX_RESULTS_PER_REQUEST', 100)),
    'delay': int(os.getenv('DELAY_BETWEEN_REQUESTS', 3))
}

# Configuration du projet
PROJECT_CONFIG = {
    'name': os.getenv('PROJECT_NAME', 'arxiv_extraction'),
    'data_dir': os.getenv('DATA_DIR', 'data/'),
    'log_dir': os.getenv('LOG_DIR', 'logs/')
}

# Catégories ArXiv disponibles
ARXIV_CATEGORIES = {
    'cs.AI': 'Computer Science - Artificial Intelligence',
    'cs.CL': 'Computer Science - Computation and Language',
    'cs.CV': 'Computer Science - Computer Vision and Pattern Recognition',
    'cs.LG': 'Computer Science - Machine Learning',
    'stat.ML': 'Statistics - Machine Learning',
    'math.ST': 'Mathematics - Statistics Theory',
    'q-bio.QM': 'Quantitative Biology - Quantitative Methods',
    'physics.data-an': 'Physics - Data Analysis, Statistics and Probability'
}

# Logging configuration
import logging
import os

def setup_logging():
    """Configure le système de logging."""
    if not os.path.exists(PROJECT_CONFIG['log_dir']):
        os.makedirs(PROJECT_CONFIG['log_dir'])
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(PROJECT_CONFIG['log_dir'], 'arxiv_extraction.log')),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)