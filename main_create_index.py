# main_create_index.py

from semantic_indexer import SemanticIndexer

if __name__ == "__main__":
    json_path = "data/extraction_results_20250718_201624.json"  # adapte selon ton fichier
    indexer = SemanticIndexer()
    indexer.index_from_json(json_path)
