def detect_intent(text):
    text = text.lower()
    if any(word in text for word in ["auteur", "qui", "écrit", "publie"]):
        return "search_by_author"
    elif any(word in text for word in ["titre", "sujet", "nommé"]):
        return "search_by_title"
    elif any(word in text for word in ["résumé", "abstract", "contenu"]):
        return "search_by_abstract"
    else:
        return "general_search"

if __name__ == "__main__":
    q = input("Question: ")
    print(f"Intention détectée: {detect_intent(q)}")
