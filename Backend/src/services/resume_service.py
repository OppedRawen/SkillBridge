
import os
from parsing.resume_parser import parse_resume_pdf
from models.model_loader import load_sentence_transformer
from sentence_transformers import util

# 1. IMPORT SkillNer
import spacy
from spacy.matcher import PhraseMatcher
from skillNer.general_params import SKILL_DB
from skillNer.skill_extractor_class import SkillExtractor

# 2. Initialize SkillNer (global or inline)
nlp = spacy.load("en_core_web_lg")
skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)

async def analyze_resume_and_job(file, job_description: str):
    """
    1. Saves the uploaded file temporarily.
    2. Parses PDF text.
    3. Performs skill extraction on resume and job description.
    4. Compares matched vs missing skills.
    5. Categorizes missing skills.
    """

    # Save the file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(file.file.read())
    
    try:
        pdf_text = parse_resume_pdf(temp_file_path)
    except Exception as e:
        os.remove(temp_file_path)
        return {"error": f"Failed to parse PDF: {str(e)}"}
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    # 3. Use SkillNer instead of load_ner_model()
    #    Extract skills from resume text
    resume_annotations = skill_extractor.annotate(pdf_text)
    # Extract skills from job description text
    job_annotations = skill_extractor.annotate(job_description)

    # 4. Parse the results to get sets of skill strings
    #    We'll combine 'full_matches' and 'ngram_scored' with a threshold
    threshold = 0.8

    def extract_skills_from_annotations(annotations):
        found_skills = set()

        # Full matches = direct phrase matches from EMSI DB
        for fm in annotations["results"]["full_matches"]:
            found_skills.add(fm["doc_node_value"].lower())

        # ngram_scored = partial matches with a score
        for ng in annotations["results"]["ngram_scored"]:
            if ng["score"] >= threshold:
                found_skills.add(ng["doc_node_value"].lower())

        return found_skills

    resume_skills = extract_skills_from_annotations(resume_annotations)
    job_skills = extract_skills_from_annotations(job_annotations)

    matched_skills = resume_skills.intersection(job_skills)
    missing_skills = job_skills.difference(resume_skills)

    # 5. Category labeling using your sentence transformer
    sentence_model = load_sentence_transformer()
    category_labels = [
        "Backend Development", "Frontend Development", "Machine Learning",
        "Soft Skills", "Tools & Platforms", "Certifications"
    ]
    category_embeddings = sentence_model.encode(category_labels, convert_to_tensor=True)

    categorized_skills = {}
    for skill in missing_skills:
        skill_embedding = sentence_model.encode(skill, convert_to_tensor=True)
        similarity_scores = util.pytorch_cos_sim(skill_embedding, category_embeddings)[0]
        top_matches = sorted(
            [(category_labels[i], score.item()) for i, score in enumerate(similarity_scores)],
            key=lambda x: x[1],
            reverse=True
        )
        categorized_skills[skill] = top_matches

    return {
        "matched_skills": list(matched_skills),
        "missing_skills": list(missing_skills),
        "categorized_missing_skills": categorized_skills
    }
