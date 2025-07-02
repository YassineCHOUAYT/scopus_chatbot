import os
from dotenv import load_dotenv

load_dotenv()

SCOPUS_API_KEY = os.getenv('SCOPUS_API_KEY')
SCOPUS_BASE_URL = "https://api.elsevier.com/content/search/scopus"
DATABASE_PATH = "scopus_data.db"
VECTOR_INDEX_PATH = "faiss_index"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"