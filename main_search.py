# main_search.py

from semantic_indexer import semantic_search

if __name__ == "__main__":
    query = "deep learning "
    semantic_search(query, top_k=1)
