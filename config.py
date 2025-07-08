import os
from dotenv import load_dotenv
import mysql.connector


load_dotenv()  

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),      
        user=os.getenv("DB_USER", "root"),            
        password=os.getenv("DB_PASSWORD", ""),         
        database=os.getenv("DB_NAME", "scopus_db"),  
        charset='utf8mb4'
    )


