 # backend/src/models/skill_matcher.py
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Load the pre-trained Sentence-BERT model
model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight version of BERT optimized for speed and accuracy

def generate_embeddings(texts):
    """
    Generate BERT embeddings for a list of text inputs.
    """
    embeddings = model.encode(texts, convert_to_tensor=True)
    return embeddings

def calculate_similarity(embedding1, embedding2):
    """
    Calculate the cosine similarity between two embeddings.
    """
    similarity = cosine_similarity([embedding1.cpu().numpy()], [embedding2.cpu().numpy()])[0][0]
    return similarity

def extract_skills_with_bert(resume_text, job_description, skill_list):
    """
    Extract and compare skills using BERT embeddings.
    - Convert both texts to embeddings.
    - Compare against skill dictionary using semantic similarity.
    """
    matched_skills = set()
    missing_skills = set()

    # Generate embeddings for the entire résumé and job description
    resume_embedding = generate_embeddings([resume_text])[0]
    job_embedding = generate_embeddings([job_description])[0]

    # Compare against each skill in the skill dictionary
    for skill_entry in skill_list:
        if isinstance(skill_entry,dict) and "name" in skill_entry:

            skill_name = skill_entry["name"]
            skill_embedding = generate_embeddings([skill_name])[0]
        
        # Calculate similarity between skill and the job description/résumé
            job_similarity = calculate_similarity(skill_embedding, job_embedding)
            resume_similarity = calculate_similarity(skill_embedding, resume_embedding)

            # If skill appears relevant in both with a high similarity score
            if job_similarity > 0.75 and resume_similarity > 0.75:
                matched_skills.add(skill_name)
            else:
                missing_skills.add(skill_name)
        else:
            print("Invalid skill entry:", skill_entry)
        

    return matched_skills, missing_skills
