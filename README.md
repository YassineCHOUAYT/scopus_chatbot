# 🤖 Scopus Chatbot

Assistant intelligent pour explorer, rechercher et analyser la littérature scientifique issue de Scopus, avec interface web, recherche sémantique et visualisations.

---

## 📦 Fonctionnalités

- **Recherche sémantique** d’articles (français/anglais)
- **Résumé automatique** et affichage des métadonnées
- **Statistiques** sur la base (articles, auteurs, années, journaux…)
- **Visualisations interactives** (évolution, top journaux, domaines…)
- **Extraction et traitement** automatisés des données Scopus
- **Interface web** conviviale (Streamlit)

---

## 🗂️ Structure du projet

```
scopus_chatbot/
│
├── app.py                # Interface web Streamlit
├── chatbot.py            # Logique du chatbot (NLP, intents, réponses)
├── semantic_search.py    # Recherche sémantique (embeddings, FAISS)
├── data_processing.py    # Nettoyage et insertion dans SQLite
├── run_project.py        # Pipeline automatisé (extraction → webapp)
├── config.py             # Paramètres globaux
├── .env                  # Clé API Scopus (à configurer)
├── scopus_raw_data.json  # Données brutes extraites (généré)
├── scopus_data.db        # Base SQLite (généré)
├── faiss_index.index     # Index sémantique FAISS (généré)
└── ...
```

---

## ⚡ Installation & Lancement

1. **Cloner le dépôt**
   ```bash
   git clone <url_du_repo>
   cd scopus_chatbot
   ```

2. **Configurer la clé API Scopus**
   - Ouvre `.env` et renseigne ta clé :
     ```
     SCOPUS_API_KEY=VOTRE_CLE_API_ICI
     ```

3. **Lancer le pipeline complet**
   ```bash
   python run_project.py
   ```
   Ce script :
   - Installe les dépendances si besoin
   - Extrait les données Scopus (API)
   - Traite et insère dans la base SQLite
   - Crée l’index sémantique
   - Lance l’interface web

---

## 🖥️ Utilisation

- Accède à l’interface web (généralement [http://localhost:8501](http://localhost:8501))
- Pose tes questions (exemples :  
  - `Trouve des articles sur l'intelligence artificielle`
  - `Statistiques de la base`
  - `Articles récents sur machine learning en 2023`
  - `Recherche par auteur Smith`
- Explore les onglets **Visualisations** et **Statistiques**

---

## 🛠️ Dépendances principales

- `pandas`, `numpy`
- `sentence-transformers`
- `faiss-cpu`
- `streamlit`, `plotly`
- `python-dotenv`
- `requests`
- `sqlite3`

Le script `run_project.py` gère leur installation.

---

## 📚 Personnalisation

- **Extraction** : adapte les requêtes dans `run_project.py` ou fournis ton propre JSON.
- **Recherche sémantique** : change le modèle dans `config.py`.
- **Visualisations** : modifie/ajoute des graphiques dans `app.py`.

---

## 📝 Remarques

- Nécessite une clé API Scopus valide ([Elsevier Developer Portal](https://dev.elsevier.com/)).
- Les données sont stockées localement.
- Pour réindexer ou retraiter, supprime les fichiers générés puis relance le script.

---

## 🤝 Contribuer

Contributions bienvenues !  
Ouvre une issue ou une pull request.

---

## 📄 Licence

Projet académique – usage pédagogique uniquement.