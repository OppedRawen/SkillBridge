import spacy
from sentence_transformers import SentenceTransformer
import os

def load_ner_model():
    """Load the fine-tuned NER model from the models directory."""
    model_path = os.path.join(os.path.dirname(__file__), "model-best")
    return spacy.load(model_path)

def load_sentence_transformer():
    """Load the fine-tuned Sentence Transformer model from the models directory."""
    model_path = os.path.join(os.path.dirname(__file__), "fine_tuned_sentence_transformer")
    return SentenceTransformer(model_path)
