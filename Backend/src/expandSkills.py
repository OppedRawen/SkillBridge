import json
import pandas as pd
from sentence_transformers import SentenceTransformer, util

# ✅ Load Sentence Transformer Model
sentence_model = SentenceTransformer("../data/fine_tuned_sentence_transformer2")

# ✅ Load Datasets from ../data directory
resume_df = pd.read_csv("../data/UpdatedResumeDataSet.csv")
job_df = pd.read_csv("../data/job_title_des.csv")

# ✅ Load Existing Skills JSON
with open("../data/new_skills.json", "r") as f:
    skills_data = json.load(f)

# ✅ Prepare Existing Skill List and Encode
skills_list = [skill["name"] for skill in skills_data["skills"]]
skill_embeddings = sentence_model.encode(skills_list, convert_to_tensor=True)

# ✅ Chunking function to break text into smaller segments
def chunk_text(text, chunk_size=100):
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

# ✅ Function to extract candidate skills by comparing against existing skill embeddings
def extract_potential_skills(dataframe, skill_embeddings, skills_list, threshold=0.5):
    potential_skills = set()
    
    for _, row in dataframe.iterrows():
        chunks = chunk_text(row["Resume"] if "Resume" in dataframe.columns else row["Job Description"])
        chunk_embeddings = sentence_model.encode(chunks, convert_to_tensor=True)
        
        for idx, chunk_embedding in enumerate(chunk_embeddings):
            similarity_scores = util.pytorch_cos_sim(chunk_embedding, skill_embeddings)[0]
            if max(similarity_scores) > threshold:
             potential_skills.add(chunks[idx])
    
    return potential_skills

# ✅ Extract Skills from Both Datasets
new_resume_skills = extract_potential_skills(resume_df, skill_embeddings, skills_list)
new_job_skills = extract_potential_skills(job_df, skill_embeddings, skills_list)

# ✅ Combine and Deduplicate Skills
expanded_skills = new_resume_skills.union(new_job_skills)
print(f"Number of new potential skills identified: {len(expanded_skills)}")


# ✅ Validate and Add Skills to the Existing Skills List
for skill in expanded_skills:
    if skill not in skills_list:  # Prevent duplicates
        skills_data["skills"].append({"name": skill, "synonyms": []})

# ✅ Save the Expanded Skills List to ../data/expanded_skills.json
with open("../data/expanded_skills.json", "w") as f:
    json.dump(skills_data, f, indent=4)

print("✅ Expanded skills have been saved to ../data/expanded_skills.json.")
