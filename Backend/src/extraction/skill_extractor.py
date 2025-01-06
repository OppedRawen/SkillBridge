import json
import os

def load_skill_dictionary():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(current_dir, '..', '..', 'data')
    skill_file_path = os.path.join(data_dir, 'skills.json')

    with open(skill_file_path,'r', encoding='utf-8') as f:
        skills = json.load(f)
    return skills

def preprocess_text(text:str)->str:
    text = text.lower()
   
    return text

def extract_skills_from_text(text: str, skills: list) -> set:
    """
    Return a set of skills found in the text by simple substring matching.
    Example: If text contains 'experience with python and docker', 
    and skills = ['python','docker'], we return {'python','docker'}.
    """
    found_skills = set()
    # Lowercase text for matching
    processed_text = preprocess_text(text)

    # Iterate through each skill in our dictionary
    for skill in skills:
        skill = skill.strip().lower()  # ensure skill is lowercase
        if skill in processed_text:
            found_skills.add(skill)
    return found_skills
