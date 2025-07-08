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

- Yassine chouayt
- [Autres contributeurs]

---

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus d’informations.

---
 
