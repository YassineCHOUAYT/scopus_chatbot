#!/usr/bin/env python3
"""
Script de lancement complet du projet Chatbot Scopus
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def check_dependencies():
    """Vérification des dépendances"""
    required_packages = [
        'pandas', 'requests', 'sentence-transformers', 
        'faiss-cpu', 'streamlit', 'plotly', 'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Packages manquants: {', '.join(missing_packages)}")
        print("Installation automatique...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
        print("✅ Installation terminée")
    else:
        print("✅ Toutes les dépendances sont installées")

def setup_environment():
    """Configuration de l'environnement"""
    # Création du fichier .env si inexistant
    if not os.path.exists('.env'):
        print("📝 Création du fichier .env...")
        with open('.env', 'w') as f:
            f.write("SCOPUS_API_KEY=your_scopus_api_key_here\n")
        print("⚠️  Veuillez configurer votre clé API Scopus dans le fichier .env")
        return False
    
    # Vérification de la clé API
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('SCOPUS_API_KEY')
    if not api_key or api_key == 'your_scopus_api_key_here':
        print("⚠️  Clé API Scopus non configurée dans .env")
        return False
    
    print("✅ Configuration environnement OK")
    return True

def extract_data():
    """Extraction des données Scopus"""
    print("🔍 Extraction des données Scopus...")
    
    try:
        from data_extraction import ScopusExtractor
        
        extractor = ScopusExtractor()
        
        # Requêtes d'exemple
        queries = [
            "artificial intelligence",
            "machine learning", 
            "deep learning",
            "natural language processing",
            "computer vision"
        ]
        
        articles = extractor.extract_multiple_queries(queries, max_results=500)
        
        # Sauvegarde
        import json
        with open('scopus_raw_data.json', 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {len(articles)} articles extraits et sauvegardés")
        return len(articles) > 0
        
    except Exception as e:
        print(f"❌ Erreur extraction: {e}")
        return False

def process_data():
    """Traitement des données"""
    print("🔄 Traitement des données...")
    
    try:
        from data_processing import DataProcessor
        
        processor = DataProcessor()
        count = processor.process_articles('scopus_raw_data.json')
        
        print(f"✅ {count} articles traités et stockés")
        return count > 0
        
    except Exception as e:
        print(f"❌ Erreur traitement: {e}")
        return False

def create_index():
    """Création de l'index sémantique"""
    print("🧠 Création de l'index sémantique...")
    
    try:
        from semantic_search import SemanticSearch
        
        search_engine = SemanticSearch()
        search_engine.create_embeddings()
        
        print("✅ Index sémantique créé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur indexation: {e}")
        return False

def test_chatbot():
    """Test du chatbot"""
    print("🤖 Test du chatbot...")
    
    try:
        from chatbot import ScopusChatbot
        
        chatbot = ScopusChatbot()
        
        # Test simple
        response = chatbot.process_query("statistiques")
        print("✅ Chatbot fonctionnel")
        return True
        
    except Exception as e:
        print(f"❌ Erreur chatbot: {e}")
        return False

def launch_app():
    """Lancement de l'application Streamlit"""
    print("🚀 Lancement de l'application...")
    
    try:
        subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'app.py'])
    except KeyboardInterrupt:
        print("\n👋 Application fermée")
    except Exception as e:
        print(f"❌ Erreur lancement: {e}")

def main():
    """Fonction principale"""
    print("🎯 Lancement du projet Chatbot Scopus")
    print("=" * 50)
    
    # Étape 1: Vérification des dépendances
    check_dependencies()
    
    # Étape 2: Configuration environnement
    if not setup_environment():
        print("❌ Configuration environnement échouée")
        return
    
    # Vérification des fichiers existants
    has_data = os.path.exists('scopus_raw_data.json')
    has_db = os.path.exists('scopus_data.db')
    has_index = os.path.exists('faiss_index.index')
    
    print(f"📊 État actuel:")
    print(f"  - Données brutes: {'✅' if has_data else '❌'}")
    print(f"  - Base de données: {'✅' if has_db else '❌'}")
    print(f"  - Index sémantique: {'✅' if has_index else '❌'}")
    
    # Processus complet ou partiel
    if not has_data:
        if not extract_data():
            print("❌ Échec extraction des données")
            return
    
    if not has_db:
        if not process_data():
            print("❌ Échec traitement des données")
            return
    
    if not has_index:
        if not create_index():
            print("❌ Échec création index")
            return
    
    # Test final
    if not test_chatbot():
        print("❌ Échec test chatbot")
        return
    
    print("\n🎉 Projet configuré avec succès!")
    print("🚀 Lancement de l'interface web...")
    
    # Lancement de l'app
    launch_app()

if __name__ == "__main__":
    main()