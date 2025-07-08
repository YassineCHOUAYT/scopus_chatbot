import streamlit as st
from semantic_search import semantic_search  # ta fonction de recherche
import pandas as pd
import plotly.express as px

# Connexion sécurisée via config.py
from config import get_connection

# Initialisation de la base de données
from database.init_db import create_tables
create_tables()

def fetch_articles_filtered(min_year=None, author=None):
    conn = get_connection()  
    cursor = conn.cursor(dictionary=True)

    query = "SELECT id, title, abstract, published, authors FROM articles WHERE 1=1"
    params = []
    if min_year:
        query += " AND YEAR(published) >= %s"
        params.append(min_year)
    if author:
        query += " AND authors LIKE %s"
        params.append(f"%{author}%")

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def display_results(results):
    for i, res in enumerate(results, 1):
        st.markdown(f"### {i}. {res['title']}")
        st.markdown(f"**Résumé:** {res['abstract'][:600]}{'...' if len(res['abstract']) > 600 else ''}")
        st.markdown(f"**Score de similarité:** {res['score']:.3f}")
        st.markdown("---")

def main():
    st.title("🤖 Chatbot Scientifique Scopus")

    user_query = st.text_input("Pose ta question scientifique ici :")

    if st.button("Rechercher") and user_query.strip():
        st.info("Recherche en cours...")

        results = semantic_search(user_query, top_k=10)

        if results:
            for i, article in enumerate(results, start=1):
                st.markdown(f"### {i}. {article['title']} (score: {article['score']:.3f})")
                st.write(article['abstract'][:600] + ("..." if len(article['abstract']) > 600 else ""))
                st.write(f"**Auteurs:** {article.get('authors', 'N/A')}")
                st.write(f"**Publié le:** {article.get('published', 'N/A')}")
                st.markdown("---")
        else:
            st.warning("Aucun résultat trouvé.")

if __name__ == "__main__":
    main()
