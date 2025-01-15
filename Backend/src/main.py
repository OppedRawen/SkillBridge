from fastapi import FastAPI, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from extraction.skill_extractor import load_skill_dictionary
from parsing.resume_parser import parse_resume_pdf
from models.model_loader import load_ner_model, load_sentence_transformer
from pydantic import BaseModel
from sentence_transformers import util
import PyPDF2
import os

app = FastAPI()

# Load models
ner_model = load_ner_model()
sentence_model = load_sentence_transformer()

# ✅ CORS Middleware for frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust if your frontend is hosted elsewhere
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Test route
@app.get("/")
def root():
    return {"message": "Skill Gap Analysis API is Running!"}

# ✅ Updated Analyze Resume Endpoint
@app.post("/analyze_resume")
async def analyze_resume(file: UploadFile = File(...), job_description: str = Form(...)):
    """Analyzes a resume and compares it with a job description."""
    # Save the uploaded file temporarily
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(file.file.read())

    # ✅ Step 1: Extract text using PDF parser
    try:
        pdf_text = parse_resume_pdf(temp_file_path)
    except Exception as e:
        os.remove(temp_file_path)
        return {"error": f"Failed to parse PDF: {str(e)}"}
    finally:
        os.remove(temp_file_path)  # Clean up the temporary file

    # ✅ Step 2: NER for both resume and job description
    resume_doc = ner_model(pdf_text)
    job_doc = ner_model(job_description)

    resume_skills = {ent.text for ent in resume_doc.ents if ent.label_ == "SKILL"}
    job_skills = {ent.text for ent in job_doc.ents if ent.label_ == "SKILL"}


    # ✅ Step 3: Identify Matched and Missing Skills
    matched_skills = resume_skills.intersection(job_skills)
    missing_skills = job_skills.difference(resume_skills)

    # ✅ Step 4: Categorize Missing Skills using Sentence Transformer
    categorized_skills = {}
    category_labels = [
        "Backend Development", "Frontend Development", "Machine Learning",
        "Soft Skills", "Tools & Platforms", "Certifications"
    ]
    category_embeddings = sentence_model.encode(category_labels, convert_to_tensor=True)

    for skill in missing_skills:
        skill_embedding = sentence_model.encode(skill, convert_to_tensor=True)
        similarity_scores = util.pytorch_cos_sim(skill_embedding, category_embeddings)[0]
        top_matches = sorted(
            [(category_labels[i], score.item()) for i, score in enumerate(similarity_scores)],
            key=lambda x: x[1], reverse=True
        )
        categorized_skills[skill] = top_matches

    # ✅ Debugging Prints for Final Output
    print("Matched Skills:", matched_skills)
    print("Missing Skills:", missing_skills)
    print("Categorized Missing Skills:", categorized_skills)

    return {
        "matched_skills": list(matched_skills),
        "missing_skills": list(missing_skills),
        "categorized_missing_skills": categorized_skills
    }

# ✅ Running the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
