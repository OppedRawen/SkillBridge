# src/main.py

# src/main.py
import os
from parsing.resume_parser import parse_resume_pdf
from utils.text_cleaning import preprocess_text
from extraction.skill_extractor import load_skill_dictionary, extract_skills_from_text

def main():

    current_dir = os.path.dirname(__file__)
    pdf_path = os.path.join(current_dir, "..", "assets", "Jake_s_Resume.pdf")
    parsed_text = parse_resume_pdf(pdf_path)
    cleaned_text = preprocess_text(parsed_text)

    skill_list = load_skill_dictionary()

    found_resume_skills =extract_skills_from_text(cleaned_text,skill_list)

    print("Skills found in resume:", found_resume_skills)
    
if __name__ == "__main__":
    main()
