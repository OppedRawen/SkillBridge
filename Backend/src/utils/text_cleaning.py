def preprocess_text(text: str) -> str:
    """
    Convert text to lowercase, remove extra whitespace, etc.
    """
    # Lowercase
    text = text.lower()
    # Remove extra whitespace
    text = " ".join(text.split())
    return text
