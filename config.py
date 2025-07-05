import os

import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="arxiv_db",
        charset='utf8mb4'
    )
