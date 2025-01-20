import os
from parsing.resume_parser import parse_resume_pdf
from models.model_loader import load_ner_model, load_sentence_transformer
from sentence_transformers import util

async def analyze_resume_and_job(file, job_description: str):
    """
    1. Saves the uploaded file temporarily.
    2. Parses PDF text.
    3. Performs NER on resume and job description.
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

    ner_model = load_ner_model()
    sentence_model = load_sentence_transformer()

    resume_doc = ner_model(pdf_text)
    job_doc = ner_model(job_description)

    resume_skills = {ent.text for ent in resume_doc.ents if ent.label_ == "SKILL"}
    job_skills = {ent.text for ent in job_doc.ents if ent.label_ == "SKILL"}

    matched_skills = resume_skills.intersection(job_skills)
    missing_skills = job_skills.difference(resume_skills)

    # Category labeling
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
