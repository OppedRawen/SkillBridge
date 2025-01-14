import spacy
from sentence_transformers import SentenceTransformer, util

# Load the trained NER model and Sentence Transformer model
nlp = spacy.load("model_output/model-best")
st_model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight sentence transformer

def extract_skills_with_ner(text):
    """Extract skills using the trained NER model."""
    doc = nlp(text)
    return [ent.text for ent in doc.ents if ent.label_ == "SKILL"]

def extract_soft_skills(text, skill_dict, threshold=0.75):
    """Identify contextually similar skills using Sentence Transformers."""
    extracted_skills = extract_skills_with_ner(text)
    skill_list = list(skill_dict.keys())  # Convert skills.json into a list of skill names
    text_embedding = st_model.encode([text], convert_to_tensor=True)
    skill_embeddings = st_model.encode(skill_list, convert_to_tensor=True)

    # Calculate cosine similarities between job description and skills list
    similarities = util.pytorch_cos_sim(text_embedding, skill_embeddings)[0]

    # Collect skills with high similarity scores
    soft_skills = []
    for idx, score in enumerate(similarities):
        if score > threshold:
            soft_skills.append(skill_list[idx])

    return set(soft_skills) - set(extracted_skills)  # Return only non-explicit matches
