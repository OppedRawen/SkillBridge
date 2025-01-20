from fastapi import APIRouter, UploadFile, File, Form
from services.resume_service import analyze_resume_and_job

router = APIRouter()

@router.get("/")
def root():
    return {"message": "Resume-related endpoints"}

@router.post("/analyze")
async def analyze_resume(file: UploadFile = File(...), job_description: str = Form(...)):
    """
    Analyzes a resume and compares it with a job description.
    """
    result = await analyze_resume_and_job(file, job_description)
    return result
