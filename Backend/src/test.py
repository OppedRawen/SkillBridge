from parsing.resume_parser import parse_resume_pdf
from models.model_loader import load_ner_model
import torch
from sentence_transformers import SentenceTransformer, util
import spacy
import json
# Initialize models
sentence_model = SentenceTransformer("../data/fine_tuned_sentence_transformer2")
ner_model = load_ner_model()

# ✅ Chunking for better performance
def chunk_text(text, chunk_size=100):
    """Breaks text into smaller chunks of roughly 'chunk_size' words."""
    words = text.split()
    chunks = [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks

with open("../data/new_skills.json", "r") as f:
    skills_data = json.load(f)
    
# Prepare the skills list and embeddings
skills_list = [skill["name"] for skill in skills_data["skills"]]
skill_embeddings = sentence_model.encode(skills_list, convert_to_tensor=True)
# ✅ NER Extraction (Direct Extraction from Resume)
def extract_skills_ner(text):
    """Extract skills using the NER model."""
    doc = ner_model(text)
    return {ent.text for ent in doc.ents if ent.label_ == "SKILL"}

# ✅ Sentence Transformer Matching Directly from the Resume
def extract_skills_semantic(text, skill_embeddings, threshold=0.8):
    chunks = chunk_text(text)
    resume_embeddings = sentence_model.encode(chunks, convert_to_tensor=True)

    matched_skills = set()
    for idx, chunk_embedding in enumerate(resume_embeddings):
        similarity_scores = util.pytorch_cos_sim(chunk_embedding, skill_embeddings)[0]
        for i, score in enumerate(similarity_scores):
            if score > threshold:
                matched_skills.add(chunks[idx])  # Return the chunk only if it matches closely

    return matched_skills

# ✅ Hybrid Extraction combining both NER and Sentence Transformer
def extract_skills_hybrid(resume_text, skill_embeddings, threshold=0.8):
    ner_skills = extract_skills_ner(resume_text)
    semantic_skills = extract_skills_semantic(resume_text, skill_embeddings, threshold)
    
    # ✅ Filter the semantic results further using a keyword approach to reduce irrelevant data
    filtered_skills = {skill for skill in semantic_skills if len(skill.split()) <= 3}

    combined_skills = ner_skills.union(filtered_skills)
    return combined_skills

# ✅ Load the Resume and Extract Skills
resume_text = parse_resume_pdf("../assets/Jake_s_Resume.pdf")
matched_skills = extract_skills_hybrid(resume_text,skill_embeddings,threshold=0.8)
print("Final Extracted Skills:", matched_skills)
