# Test de la gestion de la base de données avec Database_manager.py

Ce module permet de créer la base de données, les tables nécessaires, et d’obtenir des statistiques sur les articles et auteurs.

## Prérequis

- Python 3.8+
- MySQL/MariaDB installé et en fonctionnement
- Les identifiants de connexion sont à configurer dans `.env` ou `config.py` (voir variables `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`).

## Installation des dépendances

```bash
1. Vérifie l’environnement
pip install -r requirements.txt

2. Initialise la base de données
python main_extractor.py initdb

3. Teste l’extraction par mots-clés
python main_extractor.py extract_keywords --keywords "machine learning" --categories cs.LG cs.AI --max-results 5

4. Teste l’extraction par catégorie
python main_extractor.py extract_category --category cs.CV --max-results 3

Tu dois voir : 3 articles extraits et sauvegardés.

5. Vérifie les statistiques de la base
python main_extractor.py stats
```
