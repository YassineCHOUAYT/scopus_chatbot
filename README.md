# Chatbot Scientifique ArXiv

## Description

Ce projet est un chatbot intelligent qui permet d’interroger en langage naturel une base d’articles scientifiques issus d’ArXiv.  
Il utilise des techniques de NLP, des embeddings vectoriels (`sentence-transformers`) et une recherche sémantique pour fournir des réponses pertinentes.  
L’interface utilisateur est réalisée avec Streamlit.

---

## Fonctionnalités

- Extraction automatique des articles scientifiques depuis ArXiv via l’API.
- Stockage des données dans une base MySQL.
- Transformation des résumés en vecteurs numériques (embeddings).
- Recherche sémantique basée sur la similarité cosinus..
- Interface utilisateur avec filtres (année, auteur).
- Visualisation simple du nombre d’articles par année.

---

## Installation

1. Cloner ce dépôt :

```bash
git clone https://github.com/ton-utilisateur/scopus_chatbot.git
cd scopus_chatbot
```

2. Installer les dépendances Python :

```bash
pip install -r requirements.txt
```

3. Configurer la base de données MySQL :

- Créez une base de données nommée `arxiv_db` (ou modifiez le nom dans `config.py`).
- Mettez à jour les identifiants de connexion dans `config.py` si besoin.

4. (Optionnel) Configurer les variables d’environnement :

- Créez un fichier `.env` à la racine du projet pour stocker vos clés API si nécessaire.

---

## Utilisation

1. **Extraction des articles ArXiv** :

```bash
python arxiv_fetch.py
```

2. **Insertion dans la base MySQL** :

```bash
python insert_mysql.py
```

3. **Calcul des embeddings** :

```bash
python embedding.py
```

4. **Lancer la recherche sémantique (optionnel en CLI)** :

```bash
python semantic_search.py
```

5. **Lancer l’interface web Streamlit** :

```bash
streamlit run main.py
```

6. Ouvrez votre navigateur à l’adresse indiquée (par défaut http://localhost:8501).

---

## Structure du projet

```
scopus_chatbot/
│
├── arxiv_fetch.py          # Extraction des articles depuis ArXiv
├── insert_mysql.py         # Insertion dans la base MySQL
├── embedding.py            # Calcul des embeddings avec sentence-transformers
├── semantic_search.py      # Recherche sémantique dans la base
├── main.py                 # Interface utilisateur Streamlit
├── requirements.txt        # Dépendances Python
├── README.md               # Ce fichier
└── ...
```

---

## Exemples d’utilisation

- **Recherche d’articles par mots-clés** :  
  Posez une question comme « Quels sont les articles récents sur le deep learning ? »
- **Filtrage par année ou auteur** :  
  Utilisez les filtres de l’interface pour affiner vos résultats.
- **Visualisation** :  
  Consultez les graphiques pour voir la répartition des articles par année.

---

## Limitations

- Le projet utilise l’API ArXiv, qui ne fournit pas toujours toutes les métadonnées (ex : affiliations).
- Le stockage par défaut est MySQL, mais peut être adapté à SQLite.
- Le nombre d’articles extraits dépend des limites de l’API ArXiv.

---

## Auteurs

- [Votre nom]
- [Autres contributeurs]

---

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus d’informations.

---