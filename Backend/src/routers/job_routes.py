# Inside your existing route
from fastapi import APIRouter, UploadFile, File, Form
from services.job_description_analyzer import analyze_job_description

router = APIRouter()
@router.post("/jobAnalyzer")
async def analyzeJobs(file: UploadFile = File(...), job_description: str = Form(...)):
    # 1. Parse and analyze the resume (like you already do).
    # 2. Do your skill comparison logic (matched vs missing).
    # 3. Additionally, get the weighted skill info from job desc:
    weighted_job_skills = analyze_job_description(job_description)
    
    # For now, just print or log it
    print("Weighted job skills:", weighted_job_skills)

    return weighted_job_skills
