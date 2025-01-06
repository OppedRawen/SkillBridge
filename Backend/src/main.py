from fastapi import FastAPI, UploadFile, Form, File
from fastapi.middleware.cors import CORSMiddleware
from extraction.skill_extractor import load_skill_dictionary, extract_skills_from_text
from analysis.gap_analysis import analyze_skill_gap
import PyPDF2
from models.skill_matcher import extract_skills_with_bert

app = FastAPI()

# ✅ CORS Configuration (Add this part)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods: POST, GET, PUT, DELETE
    allow_headers=["*"],  # Allow all headers
)

@app.get("/")
def root():
    return {"message": "Skill Gap Analysis API is Running!"}

@app.post("/analyze")
async def analyze_skills(resume: UploadFile = File(...), job_description: str = Form(...)):
    # Load the skill dictionary
    skill_list = load_skill_dictionary()
    print("Loaded skill list:", skill_list) 
    # ✅ Read PDF using PyPDF2
    resume_text = ""
    try:
        reader = PyPDF2.PdfReader(resume.file)
        for page in reader.pages:
            resume_text += page.extract_text() + "\n"
    except Exception as e:
        return {"error": f"Failed to extract text from PDF: {str(e)}"}
    

    # Extract skills
    matched_skills, missing_skills = extract_skills_with_bert(resume_text, job_description, skill_list)
    # Return the results
    return {
        "matched_skills": list(matched_skills),
        "missing_skills": list(missing_skills),
    }