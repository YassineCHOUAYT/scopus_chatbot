import streamlit as st
from chatbot import ScopusChatbot
import pandas as pd

bot = ScopusChatbot()

st.title("🤖 Chatbot Scopus")

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.chat_input("Posez votre question sur les articles...")

if user_input:
    st.session_state.history.append(("Vous", user_input))
    result = bot.process_query(user_input)

    # Format résultat
    if isinstance(result, dict):  # statistiques
        st.session_state.history.append(("Bot", str(result)))
    elif isinstance(result, list):
        if not result:
            st.session_state.history.append(("Bot", "Aucun article trouvé."))
        else:
            display = "\n\n".join([f"📌 **{a['title']}**\n📝 {a['abstract']}" for a in result])
            st.session_state.history.append(("Bot", display))
    else:
        st.session_state.history.append(("Bot", str(result)))

# Afficher l'historique
for speaker, msg in st.session_state.history:
    with st.chat_message("user" if speaker == "Vous" else "assistant"):
        st.markdown(msg)
