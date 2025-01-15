import concurrent.futures
import json
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, util
from functools import partial

# Load the model once
model = SentenceTransformer("./models/fine_tuned_sentence_transformer")  # Smaller model for efficiency

def find_synonyms(skill, skills_list, skill_embeddings):
    """Find synonyms using SentenceTransformer similarity."""
    skill_embedding = model.encode(skill, convert_to_tensor=True)
    similarity_scores = util.pytorch_cos_sim(skill_embedding, skill_embeddings)[0]
    
    # Filter synonyms based on a threshold
    synonyms = [skills_list[i] for i, score in enumerate(similarity_scores) if score.item() > 0.6]
    return synonyms

if __name__ == "__main__":
    # Load the skills dataset once in the main process
    with open("../data/new_skills.json", "r") as f:
        skills_data = json.load(f)
    skill_names = [skill['name'] for skill in skills_data['skills']]
    skill_embeddings = model.encode(skill_names, convert_to_tensor=True)

    # Use partial to avoid reloading the JSON in each worker
    find_synonyms_partial = partial(find_synonyms, skills_list=skill_names, skill_embeddings=skill_embeddings)

    # Parallel execution using a smaller batch size to avoid memory issues
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        results = list(tqdm(executor.map(find_synonyms_partial, skill_names),
                            total=len(skill_names), desc="Expanding Skills"))

    # Update the skill set with synonyms
    for idx, skill in enumerate(skills_data['skills']):
        skill['synonyms'] = results[idx]

    # Save the expanded skill list
    with open("expanded_skills_parallel.json", "w") as f:
        json.dump(skills_data, f, indent=2)

    print("✅ Skill expansion completed successfully!")
