# job_description_analyzer.py

import spacy
from spacy.matcher import PhraseMatcher
from skillNer.general_params import SKILL_DB
from skillNer.skill_extractor_class import SkillExtractor

# Create / load nlp model (just do it once globally)
nlp = spacy.load("en_core_web_lg")
skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)

def compute_skill_weight(doc, skill_indices):

    keywords_required = {
    "must", "required", "mandatory", "essential", "needed",
    "necessity", "expertise", "strong", "proficiency", 
    # etc...
    }
    keywords_preferred = {
    "preferred", "nice-to-have", "plus", "beneficial", 
    "bonus", "familiarity", "desire"
    }

    base_weight = 1.0
    window_size = 5  # how many tokens to look around

    start_token = min(skill_indices)
    end_token = max(skill_indices)

    # Build context range
    left_context_start = max(0, start_token - window_size)
    right_context_end = min(len(doc), end_token + window_size + 1)

    surrounding_tokens = [t.lower_ for t in doc[left_context_start:right_context_end]]

    # If 'must' or 'required' is near, increase weight
    if any(k in surrounding_tokens for k in keywords_required):
        base_weight += 2.0
    # If 'preferred' is near, increase weight slightly
    if any(k in surrounding_tokens for k in keywords_preferred):
        base_weight += 1.0

    return base_weight

def analyze_job_description(text: str):
    """
    1. SkillNer to extract skills.
    2. Assign weights based on nearby keywords like 'must', 'required', etc.
    3. Return or print results.
    """
    # Step A: Extract annotations
    annotations = skill_extractor.annotate(text)

    # Combine full_matches & ngram_scored
    raw_skills = []  # store (skill_text, token_indices)
    threshold = 0.8

    for fm in annotations["results"]["full_matches"]:
        raw_skills.append((fm["doc_node_value"], fm["doc_node_id"]))

    for ng in annotations["results"]["ngram_scored"]:
        if ng["score"] >= threshold:
            raw_skills.append((ng["doc_node_value"], ng["doc_node_id"]))

    # Step B: Convert text to SpaCy doc for context analysis
    doc = nlp(text)

    # Step C: Calculate weights & aggregate
    skill_weights = {}
    for skill_text, token_indices in raw_skills:
        weight = compute_skill_weight(doc, token_indices)
        lower_skill = skill_text.lower()

        # If skill is repeated, you might sum or take max
        if lower_skill not in skill_weights:
            skill_weights[lower_skill] = weight
        else:
            skill_weights[lower_skill] = max(skill_weights[lower_skill], weight)

    # Return the skill_weights dict or print it
    return skill_weights

if __name__ == "__main__":
    # Simple test
    job_desc = """
    We are looking for a Python developer who must have React.js experience.
    Knowledge of Docker is preferred. AWS is required as well.
    """
    results = analyze_job_description(job_desc)
    print("Weighted Skills:", results)
