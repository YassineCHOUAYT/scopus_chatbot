import warnings
warnings.filterwarnings("ignore", message="Tried to instantiate class '__path__._path'")

import streamlit as st
from chatbot import EnhancedArticleSearcher
import json

# Fonctions principales
def display_article_results(search_result):
    """Affiche les résultats d'articles de manière claire et moderne"""
    results = search_result.get("results", [])
    search_info = search_result.get("search_info", {})
    
    # Affichage du header de résultats
    st.subheader(f"🔍 {len(results)} résultats pour : {search_info.get('keywords', 'votre recherche')}")
    
    if not results:
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(":mag:", width=60)
        with col2:
            st.write("""
            **Aucun résultat trouvé**  
            Essayez avec :
            - Des termes plus précis
            - Le nom complet d'un auteur
            - Des mots-clés en anglais
            """)
        return

    for i, result in enumerate(results[:5], 1):
        article = result["article"]
        with st.expander(f"{i}. {article.get('title', 'Titre inconnu')}", expanded=False):
            # Section Auteurs
            authors = ", ".join([a.get('name', '') for a in article.get('authors', [])])
            if authors:
                st.caption(f"👤 **Auteurs** : {authors}")
            
            # Section Résumé
            abstract = article.get('abstract', article.get('summary', ''))
            if abstract:
                st.write("📝 **Résumé** :")
                st.write(f"{abstract[:300]}...")
            
            # Métadonnées
            col1, col2, col3 = st.columns(3)
            if article.get('published_date'):
                col1.metric("📅 Année", article.get('published_date', '')[:4])
            
            if article.get('categories'):
                col2.metric("🏷️ Catégories", ", ".join(article.get('categories', [])[:2]))
            
            relevance = result.get('relevance', 0)
            if relevance > 0:
                col3.metric("📈 Pertinence", f"{relevance:.1f}%")
            
            # Liens
            if article.get('pdf_link') or article.get('url'):
                st.write("🔗 **Liens** :")
                cols = st.columns(4)
                if article.get('pdf_link'):
                    cols[0].markdown(f"[PDF]({article.get('pdf_link')})")
                if article.get('url'):
                    cols[1].markdown(f"[Article]({article.get('url')})")

def process_query(query):
    """Traite une requête standard avec meilleure gestion des cas sans résultats"""
    # Nettoyage de la requête
    cleaned_query = ' '.join([word for word in query.split() 
                            if len(word) > 2 and any(c.isalpha() for c in word)])
    
    st.session_state.selected_query = None
    st.session_state.messages.append({"role": "user", "content": query})
    st.session_state.history.append(query)
    
    with st.spinner("🔍 Analyse de votre requête en cours..."):
        try:
            if not cleaned_query:
                response = {
                    "results": [],
                    "search_info": {
                        "type": "invalid_query",
                        "keywords": query,
                        "suggestion": "Votre requête ne contient pas de termes valides"
                    }
                }
            else:
                result = chatbot.search(cleaned_query, top_k=5)
                response = result if result.get("results") else {
                    "results": [],
                    "search_info": {
                        "type": "no_results",
                        "keywords": cleaned_query,
                        "suggestion": "Essayez avec des termes plus spécifiques"
                    }
                }
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        except Exception as e:
            error_msg = f"❌ Erreur technique: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.rerun()

def process_advanced_query(query):
    """Traite une requête avancée avec plus de détails"""
    st.session_state.selected_query = None
    st.session_state.messages.append({"role": "user", "content": f"[Recherche avancée] {query}"})
    st.session_state.history.append(query)
    
    with st.spinner("🔍 Recherche avancée en cours..."):
        try:
            search_info = chatbot.detect_search_type(query)
            
            if search_info['type'] == 'author' and search_info['authors']:
                author = search_info['authors'][0]
                response = {
                    "type": "author_stats",
                    "author": author,
                    "articles": chatbot.get_articles_by_author(author)[:5],
                    "stats": chatbot.get_author_stats(author),
                    "search_info": search_info
                }
            else:
                response = chatbot.search(query, top_k=5)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
        except Exception as e:
            error_msg = f"❌ Erreur lors de la recherche avancée: {str(e)}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.rerun()

# Configuration de l'application
st.set_page_config(
    page_title="Academic Search Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Un assistant de recherche académique intelligent"
    }
)

# CSS personnalisé
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --primary-color: #4a6fa5;
        --primary-hover: #3a5a8f;
        --secondary-color: #6c8fc7;
        --bg-color: #ffffff;
        --chat-bg: #f8f9fa;
        --user-bg: #e9f0fb;
        --text-primary: #2d3748;
        --text-secondary: #4a5568;
        --border-color: #e2e8f0;
        --shadow: 0 2px 12px rgba(0,0,0,0.1);
        --radius: 12px;
        --accent-color: #4299e1;
    }

    .stApp {
        background: var(--bg-color);
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }

    .chat-container {
        background: var(--chat-bg);
        border-radius: var(--radius);
        padding: 1.5rem;
        box-shadow: var(--shadow);
        border: 1px solid var(--border-color);
        margin-bottom: 2rem;
    }

    .user-message {
        background: var(--user-bg);
        color: var(--text-primary);
        margin-left: 20%;
        border-radius: var(--radius);
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid var(--primary-color);
        box-shadow: var(--shadow);
    }

    .bot-message {
        background: white;
        color: var(--text-primary);
        margin-right: 20%;
        border-radius: var(--radius);
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow);
    }

    .article-card {
        background: white;
        border-radius: var(--radius);
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid var(--border-color);
        box-shadow: var(--shadow);
        transition: transform 0.2s;
    }

    .article-card:hover {
        transform: translateY(-2px);
    }

    .stTextInput>div>div>input {
        background: white;
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius);
        padding: 0.75rem 1rem;
    }

    .stButton>button {
        background: var(--primary-color);
        color: white;
        border: none;
        border-radius: var(--radius);
        padding: 0.75rem 1.5rem;
        transition: all 0.2s;
        font-weight: 500;
    }

    .stButton>button:hover {
        background: var(--primary-hover);
        transform: translateY(-1px);
    }

    .st-expander {
        border: 1px solid var(--border-color) !important;
        border-radius: var(--radius) !important;
        margin-bottom: 1rem;
    }

    .st-expander .streamlit-expanderHeader {
        font-weight: 600;
        color: var(--primary-color);
    }

    a {
        color: var(--primary-color) !important;
        text-decoration: none !important;
        font-weight: 500;
    }

    a:hover {
        text-decoration: underline !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation du chatbot
@st.cache_resource
def load_chatbot():
    try:
        return EnhancedArticleSearcher("arxiv_index.faiss", "arxiv_metadata.json")
    except Exception as e:
        st.error(f"Erreur de chargement : {e}")
        return None

chatbot = load_chatbot()

# Initialisation de l'état de session
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "selected_query" not in st.session_state:
    st.session_state.selected_query = None

# Interface utilisateur
with st.sidebar:
    st.markdown("## 🔍 Research Assistant")
    st.markdown("Recherchez des articles scientifiques et explorez les travaux d'auteurs")

    st.markdown("### 📚 Historique des requêtes")
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history[-10:])):
            if st.button(
                f"{i+1}. {item[:30]}{'...' if len(item) > 30 else ''}",
                key=f"hist_{i}",
                use_container_width=True,
                help=item
            ):
                st.session_state.selected_query = item
                st.rerun()
    else:
        st.markdown("_Aucune requête récente_")

    st.markdown("---")
    
    if st.button("🔄 Nouvelle conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.selected_query = None
        st.rerun()

    st.markdown("---")
    st.markdown("### 💡 Exemples de requêtes")
    examples = [
        "Articles de Yann LeCun sur le deep learning",
        "Recherches récentes sur les transformers",
        "Publications de Geoffrey Hinton en 2020-2023",
        "Papers sur la computer vision avec correspondance auteur"
    ]
    
    for example in examples:
        if st.button(
            f"\"{example[:20]}...\"",
            key=f"ex_{example[:5]}",
            help=example,
            use_container_width=True
        ):
            st.session_state.selected_query = example
            st.rerun()

# Zone de chat principale
col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-message">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            if isinstance(msg["content"], dict) and "results" in msg["content"]:
                display_article_results(msg["content"])
            else:
                st.markdown(f'<div class="bot-message">{msg["content"]}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Formulaire de recherche
    with st.form("query_form", clear_on_submit=True):
        query = st.text_input(
            "Posez votre question sur les articles ou auteurs", 
            value=st.session_state.selected_query or "",
            placeholder="Ex: Articles de Hanqin Cai sur la matrix completion"
        )
        col1, col2, col3 = st.columns([2,1,1])
        with col2:
            submitted = st.form_submit_button("🔍 Rechercher")
        

    if submitted and query:
        process_query(query)
    

# Point d'entrée principal
if __name__ == "__main__":
    if chatbot is None:
        st.error("Le chatbot n'a pas pu être chargé. Vérifiez les fichiers d'index.")