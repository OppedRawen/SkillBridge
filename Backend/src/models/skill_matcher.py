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
    matched_skills = set()
    missing_skills = set()

    # Generate embeddings for each token separately
    resume_tokens = resume_text.split()
    job_tokens = job_description.split()
    
    resume_embeddings = generate_embeddings(resume_tokens)
    job_embeddings = generate_embeddings(job_tokens)

    # Compare against each skill in the skill dictionary
    for skill_entry in skill_list:
        if isinstance(skill_entry, dict) and "name" in skill_entry:
            skill_name = skill_entry["name"]
            skill_embedding = generate_embeddings([skill_name])[0]
            
            # Calculate similarity with individual tokens instead of full vectors
            job_similarity = max(calculate_similarity(skill_embedding, emb) for emb in job_embeddings)
            resume_similarity = max(calculate_similarity(skill_embedding, emb) for emb in resume_embeddings)

            print(f"Skill: {skill_name} | Job Similarity: {job_similarity:.4f} | Resume Similarity: {resume_similarity:.4f}")

            if job_similarity > 0.65 and resume_similarity > 0.65:
                matched_skills.add(skill_name)
            else:
                missing_skills.add(skill_name)

    return matched_skills, missing_skills
    """
    Extract and compare skills using BERT embeddings.
    - Break down texts into words for better comparison.
    - Compare each skill term individually against words in the resume and job description.
    """
    matched_skills = set()
    missing_skills = set()

    # Tokenize (split by words) instead of using sentences
    resume_tokens = resume_text.split()
    job_tokens = job_description.split()

    # Generate embeddings for the tokenized texts
    resume_embeddings = generate_embeddings(resume_tokens)
    job_embeddings = generate_embeddings(job_tokens)

    # Compare against each skill in the skill dictionary
    for skill_entry in skill_list:
        if isinstance(skill_entry, dict) and "name" in skill_entry:
            all_skill_terms = [skill_entry["name"]] + skill_entry.get("related_terms", [])
            skill_embeddings = generate_embeddings(all_skill_terms)

            skill_matched = False  # Flag to avoid redundant matching

            for skill_embedding in skill_embeddings:
                # Compare against every word in the resume and job description
                for token_embedding in resume_embeddings + job_embeddings:
                    similarity = calculate_similarity(skill_embedding, token_embedding)
                    
                    # Debugging Output (Optional for Testing)
                    print(f"Testing skill: {skill_entry['name']}, Similarity: {similarity:.4f}")

                    if similarity > 0.65:  # Lower threshold for word-level comparison
                        matched_skills.add(skill_entry["name"])
                        skill_matched = True
                        break  # Stop comparing once a match is found
                
                if skill_matched:
                    break  # Stop checking other terms if a match is already found

            if not skill_matched:
                missing_skills.add(skill_entry["name"])

    return matched_skills, missing_skills
