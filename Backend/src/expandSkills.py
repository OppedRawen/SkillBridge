import json
import pandas as pd
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, util
from models.model_loader import load_ner_model
import spacy

# Load Sentence Transformer and NER Model
sentence_model = SentenceTransformer("../data/fine_tuned_sentence_transformer2")
sentence_model.to('cuda')
ner_model = load_ner_model()

# Load datasets
resume_df = pd.read_csv("../data/UpdatedResumeDataSet.csv")
job_df = pd.read_csv("../data/job_title_des.csv")

# Load existing skills.json
with open("../data/new_skills.json", "r") as f:
    skills_data = json.load(f)
skills_list = [skill["name"] for skill in skills_data["skills"]]
skill_embeddings = sentence_model.encode(skills_list, convert_to_tensor=True)

# Chunking function to process text in manageable sizes
def chunk_text(text, chunk_size=200):
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

# Extract skills using NER model
def extract_skills_ner(text):
    doc = ner_model(text)
    return {ent.text for ent in doc.ents if ent.label_ == "SKILL"}

# Validate skills using Sentence Transformer
def validate_skills(candidate_skills, skill_embeddings, skills_list, threshold=0.6):
    validated_skills = set()
    for skill in candidate_skills:
        skill_embedding = sentence_model.encode(skill, convert_to_tensor=True)
        similarity_scores = util.pytorch_cos_sim(skill_embedding, skill_embeddings)[0]
        max_score = max(similarity_scores)
        if max_score > threshold:
            validated_skills.add(skill)
    return validated_skills

# Hybrid approach: NER + Transformer validation
def hybrid_extract_skills(dataframe, skill_embeddings, skills_list, threshold=0.6):
    all_skills = set()
    for _, row in tqdm(dataframe.iterrows(), total=len(dataframe), desc="Processing rows"):
        text = row["Resume"] if "Resume" in dataframe.columns else row["Job Description"]
        chunks = chunk_text(text)
        for chunk in chunks:
            # NER extraction
            ner_skills = extract_skills_ner(chunk)
            # Validate NER skills
            validated_skills = validate_skills(ner_skills, skill_embeddings, skills_list, threshold)
            all_skills.update(validated_skills)
    return all_skills

# Run hybrid extraction on both datasets
print("Extracting skills from resumes...")
resume_skills = hybrid_extract_skills(resume_df, skill_embeddings, skills_list)
print("Extracting skills from job descriptions...")
job_skills = hybrid_extract_skills(job_df, skill_embeddings, skills_list)

# Combine and deduplicate skills
new_skills = resume_skills.union(job_skills)
existing_skills = set(skills_list)
expanded_skills = [skill for skill in new_skills if skill not in existing_skills]

# Update skills.json with new skills
for skill in expanded_skills:
    skills_data["skills"].append({"name": skill, "synonyms": []})

# Save expanded skills.json
with open("../data/expanded_skills.json", "w") as f:
    json.dump(skills_data, f, indent=4)

