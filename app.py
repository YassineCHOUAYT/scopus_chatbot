# app.py
import streamlit as st
from chatbot import ScopusChatbot
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Scopus Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {
        --primary-color: #10a37f;
        --secondary-color: #19c37d;
        --bg-color: #343541;
        --chat-bg: #444654;
        --user-bg: #343541;
        --text-primary: #ffffff;
        --text-secondary: #d1d5db;
        --border-color: #565869;
        --shadow: 0 2px 8px rgba(0,0,0,0.15);
    }

    .stApp {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        font-family: 'Inter', sans-serif;
    }

    .chat-container {
        background: var(--chat-bg);
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: var(--shadow);
        border: 1px solid var(--border-color);
    }

    .user-message, .bot-message {
        padding: 1rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
    }

    .user-message {
        background: var(--primary-color);
        color: white;
        margin-left: auto;
    }

    .bot-message {
        background: var(--user-bg);
        color: var(--text-primary);
        margin-right: auto;
        border: 1px solid var(--border-color);
    }
</style>
""", unsafe_allow_html=True)

# Cache chatbot
@st.cache_resource
def load_chatbot():
    try:
        return ScopusChatbot()
    except Exception as e:
        st.error(f"Erreur de chargement : {e}")
        return None

chatbot = load_chatbot()

# Etat de session
if "messages" not in st.session_state:
    st.session_state.messages = []
if "keywords_history" not in st.session_state:
    st.session_state.keywords_history = []
if "history" not in st.session_state:
    st.session_state.history = []
if "selected_query" not in st.session_state:
    st.session_state.selected_query = None

# Sidebar simple
with st.sidebar:
    st.markdown("## 💬 Historique")
    if st.session_state.history:
        for item in reversed(st.session_state.history[-10:]):
            if st.button(item[:40], key=item):
                st.session_state.selected_query = item
                st.rerun()
    else:
        st.markdown("_Aucune requête pour l'instant._")

    if st.button("➕ Nouvelle conversation"):
        st.session_state.messages = []
        st.session_state.keywords_history = []
        st.session_state.selected_query = None
        st.rerun()

# Centre du chat
col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    for msg in st.session_state.messages:
        role_class = "user-message" if msg["role"] == "user" else "bot-message"
        st.markdown(f'<div class="{role_class}">{msg["content"]}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    with st.form("query_form", clear_on_submit=True):
        query = st.text_input("Posez votre question", value=st.session_state.selected_query or "", placeholder="Ex: travaux de Yann LeCun")
        submitted = st.form_submit_button("Envoyer")

    if submitted and query:
        st.session_state.selected_query = None
        st.session_state.messages.append({"role": "user", "content": query})
        st.session_state.history.append(query)
        with st.spinner("Recherche en cours..."):
            try:
                if hasattr(chatbot, 'process_query'):
                    result, keywords = chatbot.process_query(query)
                    st.session_state.keywords_history.append(keywords)
                else:
                    result = chatbot.process_query(query)
                    keywords = []

                response = ""
                if isinstance(result, list) and result:
                    for article in result[:5]:
                        title = article.get("title", "(Titre manquant)")
                        date = article.get("published_date", "?")
                        response += f"<p><b>{title}</b><br><i>{date}</i></p>"
                else:
                    response += "<p>Aucun résultat trouvé.</p>"

                st.markdown(f'<div class="bot-message">{response}</div>', unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                err = f"Erreur : {str(e)}"
                st.markdown(f'<div class="bot-message">{err}</div>', unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": err})
