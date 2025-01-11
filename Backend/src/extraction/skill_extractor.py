import json
import os

def load_skill_dictionary():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, '..', '..', 'data')
    skill_file_path = os.path.join(data_dir, 'skills.json')

    with open(skill_file_path,'r', encoding='utf-8') as f:
        skills_data = json.load(f)
    return skills_data["skills"]

def preprocess_text(text:str)->str:
    text = text.lower()
   
    return text

def extract_skills_from_text(text: str, skills: list) -> set:
    """
    Enhanced skill extractor using 'name' and 'related_terms' from the skill dictionary.
    """
    found_skills = set()
    processed_text = text.lower()

    for skill_entry in skills:
        skill_name = skill_entry["name"].lower()
        related_terms = [term.lower() for term in skill_entry.get("related_terms", [])]

        # Check both skill name and related terms
        if skill_name in processed_text or any(term in processed_text for term in related_terms):
            found_skills.add(skill_name)

    return found_skills
