import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
from datetime import datetime
import numpy as np

from chatbot import ScopusChatbot
from config import DATABASE_PATH

# Configuration de la page
st.set_page_config(
    page_title="Chatbot Scopus",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation du chatbot
@st.cache_resource
def load_chatbot():
    return ScopusChatbot()

# Chargement des données pour visualisations
@st.cache_data
def load_data_for_viz():
    conn = sqlite3.connect(DATABASE_PATH)
    
    # Articles par année
    query_years = '''
        SELECT SUBSTR(publication_date, 1, 4) as year, COUNT(*) as count
        FROM articles
        WHERE publication_date IS NOT NULL
        GROUP BY year
        ORDER BY year
    '''
    df_years = pd.read_sql_query(query_years, conn)
    
    # Top journals
    query_journals = '''
        SELECT journal, COUNT(*) as count
        FROM articles
        WHERE journal IS NOT NULL AND journal != ''
        GROUP BY journal
        ORDER BY count DESC
        LIMIT 10
    '''
    df_journals = pd.read_sql_query(query_journals, conn)
    
    # Domaines de recherche
    query_subjects = '''
        SELECT subject_areas, COUNT(*) as count
        FROM articles
        WHERE subject_areas IS NOT NULL AND subject_areas != ''
        GROUP BY subject_areas
        ORDER BY count DESC
        LIMIT 15
    '''
    df_subjects = pd.read_sql_query(query_subjects, conn)
    
    conn.close()
    return df_years, df_journals, df_subjects

def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 Chatbot Scopus</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("🔧 Options")
    
    # Sélection du mode
    mode = st.sidebar.selectbox(
        "Mode d'utilisation",
        ["💬 Chat", "📊 Visualisations", "📈 Statistiques"]
    )
    
    # Chargement du chatbot
    try:
        chatbot = load_chatbot()
    except Exception as e:
        st.error(f"Erreur lors du chargement du chatbot: {e}")
        st.stop()
    
    if mode == "💬 Chat":
        chat_interface(chatbot)
    elif mode == "📊 Visualisations":
        visualizations_interface()
    elif mode == "📈 Statistiques":
        statistics_interface(chatbot)

def chat_interface(chatbot):
    st.header("💬 Interface de Chat")
    
    # Initialisation de l'historique
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Affichage des messages précédents
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'''
            <div class="chat-message user-message">
                <strong>🧑 Vous:</strong> {message["content"]}
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div class="chat-message bot-message">
                <strong>🤖 Assistant:</strong><br>{message["content"]}
            </div>
            ''', unsafe_allow_html=True)
    
    # Zone de saisie
    user_input = st.text_input("Posez votre question:", key="user_input")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📤 Envoyer"):
            if user_input:
                process_user_input(chatbot, user_input)
    
    with col2:
        if st.button("🗑️ Effacer"):
            st.session_state.messages = []
            st.rerun()
    
    # Suggestions de questions
    st.subheader("💡 Suggestions de questions")
    
    suggestions = [
        "Trouve des articles sur l'intelligence artificielle",
        "Statistiques de la base de données",
        "Articles récents sur machine learning",
        "Recherche des publications sur deep learning en 2023",
        "Quels sont les journaux les plus populaires ?"
    ]
    
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(suggestion, key=f"suggestion_{i}"):
                process_user_input(chatbot, suggestion)

def process_user_input(chatbot, user_input):
    # Ajout du message utilisateur
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Traitement de la requête
    with st.spinner("🔍 Recherche en cours..."):
        try:
            response = chatbot.process_query(user_input)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            error_msg = f"Désolé, une erreur s'est produite: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    st.rerun()

def visualizations_interface():
    st.header("📊 Visualisations des Données")
    
    try:
        df_years, df_journals, df_subjects = load_data_for_viz()
        
        # Graphique évolution temporelle
        st.subheader("📈 Évolution des Publications par Année")
        if not df_years.empty:
            fig_years = px.line(df_years, x='year', y='count', 
                              title="Nombre de publications par année",
                              labels={'year': 'Année', 'count': 'Nombre de publications'})
            fig_years.update_layout(height=400)
            st.plotly_chart(fig_years, use_container_width=True)
        else:
            st.info("Aucune donnée temporelle disponible")
        
        # Top journaux
        st.subheader("📖 Top 10 des Journaux")
        if not df_journals.empty:
            fig_journals = px.bar(df_journals, x='count', y='journal', 
                                orientation='h',
                                title="Journaux les plus fréquents",
                                labels={'count': 'Nombre d\'articles', 'journal': 'Journal'})
            fig_journals.update_layout(height=500)
            st.plotly_chart(fig_journals, use_container_width=True)
        else:
            st.info("Aucune donnée de journaux disponible")
        
        # Domaines de recherche
        st.subheader("🔬 Domaines de Recherche")
        if not df_subjects.empty:
            # Préparation des données pour le graphique en secteurs
            df_subjects_clean = df_subjects.head(10)  # Top 10 seulement
            
            fig_subjects = px.pie(df_subjects_clean, values='count', names='subject_areas',
                                title="Répartition par domaines de recherche")
            fig_subjects.update_layout(height=500)
            st.plotly_chart(fig_subjects, use_container_width=True)
        else:
            st.info("Aucune donnée de domaines disponible")
            
    except Exception as e:
        st.error(f"Erreur lors du chargement des visualisations: {e}")

def statistics_interface(chatbot):
    st.header("📈 Statistiques Détaillées")
    
    try:
        # Récupération des statistiques
        stats = chatbot.get_statistics()
        
        # Métriques principales
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f'''
            <div class="metric-card">
                <h3>📚 Articles</h3>
                <h2>{stats['total_articles']:,}</h2>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'''
            <div class="metric-card">
                <h3>👥 Auteurs</h3>
                <h2>{stats['total_authors']:,}</h2>
            </div>
            ''', unsafe_allow_html=True)
        
        with col3:
            avg_articles_per_author = stats['total_articles'] / max(stats['total_authors'], 1)
            st.markdown(f'''
            <div class="metric-card">
                <h3>📊 Moyenne</h3>
                <h2>{avg_articles_per_author:.1f}</h2>
                <p>articles/auteur</p>
            </div>
            ''', unsafe_allow_html=True)
        
        # Tableaux détaillés
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Années les Plus Productives")
            if stats['top_years']:
                years_df = pd.DataFrame(stats['top_years'], columns=['Année', 'Nombre d\'articles'])
                st.dataframe(years_df, use_container_width=True)
            else:
                st.info("Aucune donnée d'années disponible")
        
        with col2:
            st.subheader("📖 Journaux les Plus Actifs")
            if stats['top_journals']:
                journals_df = pd.DataFrame(stats['top_journals'], columns=['Journal', 'Nombre d\'articles'])
                st.dataframe(journals_df, use_container_width=True)
            else:
                st.info("Aucune donnée de journaux disponible")
        
        # Graphique de répartition
        if stats['top_years']:
            st.subheader("📊 Répartition Temporelle")
            years_data = pd.DataFrame(stats['top_years'], columns=['year', 'count'])
            
            fig = go.Figure(data=[
                go.Bar(x=years_data['year'], y=years_data['count'],
                      marker_color='lightblue')
            ])
            fig.update_layout(
                title="Distribution des publications par année",
                xaxis_title="Année",
                yaxis_title="Nombre de publications",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Erreur lors du chargement des statistiques: {e}")

if __name__ == "__main__":
    main()