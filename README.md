
# 🧠 Assistant de Recherche Scopus - Projet Python

Ce projet est un assistant intelligent pour explorer les articles scientifiques d'ArXiv, indexés dans une base de données MySQL. Il permet d'effectuer des recherches par mots-clés ou sémantique via une interface utilisateur Streamlit.

---

## 📁 Architecture du projet

```
.
├── .env                         # Variables d’environnement (DB, API key)
├── .gitignore
├── app.py                      # Interface utilisateur Streamlit
├── arxiv_extractor.py          # Extraction des articles via l'API ArXiv
├── arxiv_index.faiss           # Index vectoriel FAISS
├── arxiv_metadata.json         # Données brutes extraites
├── chatbot.py                  # Moteur de traitement de requêtes (logiciel)
├── config.py                   # Configuration (connexion DB, chemins)
├── data_cleaner.py             # Nettoyage des données
├── database_manager.py         # Création de la base et statistiques
├── main_create_index.py        # Génération de l’index sémantique FAISS
├── main_extractor.py           # Script CLI pour extraction / stats
├── main_search.py              # Recherche dans l’index FAISS
├── README.md
├── requirements.txt            # Dépendances Python
└── semantic_indexer.py         # Création et recherche dans l’index sémantique
```

---

## ✅ Prérequis

- Python 3.8+
- MySQL/MariaDB
- Configurer `.env` ou `config.py` avec : `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`

---

## ⚙️ Installation et premiers tests

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Créer la base de données et les tables
python main_extractor.py initdb

# 3. Extraire des articles par mots-clés
python main_extractor.py extract_keywords --keywords "machine learning" --categories cs.LG cs.AI --max-results 5

# 4. Extraire des articles par catégorie
python main_extractor.py extract_category --category cs.CV --max-results 3

# 5. Vérifier les statistiques de la base
python main_extractor.py stats
```

---

## 🔍 Indexation sémantique des résumés

Pour améliorer la recherche, les résumés sont transformés en **vecteurs sémantiques** à l’aide du modèle `all-MiniLM-L6-v2` (Sentence Transformers).

Les vecteurs sont indexés avec **FAISS** pour des recherches ultra-rapides par similarité.

### Fichiers liés

- `semantic_indexer.py` : indexation et recherche vectorielle
- `main_create_index.py` : création de l’index FAISS à partir d’un `.json`
- `main_search.py` : recherche d’articles similaires à une question

### Exemple

```bash
python main_create_index.py --json-path data/extraction_results_20250714_102000.json 'remplace par le fichier générer'
```

---

## 🧪 Interface Utilisateur Streamlit

Lance l’interface simple de chat avec :

```bash
python -m streamlit run app.py
```

- L’historique des requêtes est à gauche.
- L’utilisateur pose ses questions au centre.
- La réponse (liste d’articles) s’affiche automatiquement.

### Fichiers impliqués

- `app.py` : Interface principale (design, gestion d’historique, chat)
- `chatbot.py` : Traitement de la requête, analyse des mots, retour articles

---

## 💡 Exemples d'utilisation

- **" Yann LeCun ?"**
- **"l’intelligence artificielle"**


---

## ⚠️ Limitations

- API ArXiv ne donne pas toujours les affiliations ou les résumés complets.
- Max 10000 résultats selon l’API.
- La qualité dépend des catégories choisies (`cs.AI`, `cs.LG`, etc).

---

## 👨‍💻 Auteurs

- Yassine Chouayt
- [Autres contributeurs]

---
