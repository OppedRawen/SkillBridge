import logging
import os
import tempfile
import traceback

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from agents.enhanced_gap_agent import EnhancedGapAnalyzer
from agents.gap_agent import identify_skill_gaps
from agents.resource_agent import get_learning_resources
from services.optimized_job_analyzer import analyze_job_description, analyze_resume
from utils.numpy_converter import convert_numpy_to_python
from utils.pdf_utils import extract_text_from_pdf

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    responses={404: {"description": "Not found"}},
)

# Lazy singleton — loaded on first semantic request so startup stays fast
_semantic_analyzer: EnhancedGapAnalyzer | None = None


def _get_semantic_analyzer() -> EnhancedGapAnalyzer:
    global _semantic_analyzer
    if _semantic_analyzer is None:
        logger.info("Loading sentence-transformer model for semantic analysis…")
        _semantic_analyzer = EnhancedGapAnalyzer(similarity_threshold=0.7)
    return _semantic_analyzer


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/test")
async def test_endpoint():
    """Health-check: confirms the Jobs router is reachable."""
    return {"message": "Jobs API is working!"}


@router.post("/jobAnalyzer")
async def job_analyzer(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    use_semantic: bool = Form(True),
):
    """
    Analyse a resume against a job description and return a skill-gap breakdown.

    Multipart form fields:
      file            — PDF resume
      job_description — raw job-description text
      use_semantic    — true (default): cosine-similarity matching;
                        false: exact string matching only
    """
    temp_path: str | None = None

    try:
        # ----------------------------------------------------------------
        # 1. Validate inputs before touching the file
        # ----------------------------------------------------------------
        jd = (job_description or "").strip()
        if not jd:
            raise HTTPException(status_code=422, detail="job_description cannot be empty.")
        if len(jd) < 50:
            raise HTTPException(
                status_code=422,
                detail="job_description is too short — please provide a full job posting (≥50 characters).",
            )

        logger.info(
            "Analysis request: file=%s  jd_chars=%d  semantic=%s",
            file.filename, len(jd), use_semantic,
        )

        # ----------------------------------------------------------------
        # 2. Save the uploaded PDF to a temp file
        # ----------------------------------------------------------------
        raw_bytes = await file.read()
        if not raw_bytes:
            raise HTTPException(status_code=422, detail="Uploaded file is empty.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(raw_bytes)
            temp_path = tmp.name

        # ----------------------------------------------------------------
        # 3. Extract text from PDF
        # ----------------------------------------------------------------
        resume_text = extract_text_from_pdf(temp_path)

        if resume_text.startswith("Error") or resume_text.startswith("No text"):
            return convert_numpy_to_python({
                "status": "error",
                "message": (
                    "Could not extract text from the uploaded PDF. "
                    "Please make sure it is a text-based (not scanned/image) PDF."
                ),
                "llm_output": None,
            })

        if len(resume_text.strip()) < 50:
            return convert_numpy_to_python({
                "status": "error",
                "message": (
                    "The extracted resume text is too short to analyse. "
                    "Check that your PDF contains selectable text rather than scanned images."
                ),
                "llm_output": None,
            })

        # ----------------------------------------------------------------
        # 4. Extract skills from both documents
        # ----------------------------------------------------------------
        job_skills = analyze_job_description(jd)
        resume_skills = analyze_resume(resume_text)

        if not job_skills:
            return convert_numpy_to_python({
                "status": "error",
                "message": (
                    "No recognisable technical skills were found in the job description. "
                    "Please provide a more detailed posting."
                ),
                "llm_output": None,
            })

        logger.info(
            "Extracted %d job skills and %d resume skills",
            len(job_skills), len(resume_skills),
        )

        # ----------------------------------------------------------------
        # 5. Gap analysis
        # ----------------------------------------------------------------
        if use_semantic:
            gap_analysis = _get_semantic_analyzer().identify_semantic_skill_gaps(
                job_skills, resume_skills
            )
            analysis_type = "semantic"
        else:
            gap_analysis = identify_skill_gaps(job_skills, resume_skills)
            analysis_type = "exact"

        # ----------------------------------------------------------------
        # 6. Learning resources (best-effort — never blocks the response)
        # ----------------------------------------------------------------
        learning_resources = get_learning_resources(
            gap_analysis.get("missing_skills", {}), jd
        )

        # ----------------------------------------------------------------
        # 7. Build and return response
        # ----------------------------------------------------------------
        response_data = {
            "status": "success",
            "file_name": file.filename,
            "analysis_type": analysis_type,
            "analysis": {
                "job_skills": job_skills,
                "resume_skills": resume_skills,
                "matching_skills": gap_analysis.get("matching_skills", {}),
                "missing_skills": gap_analysis.get("missing_skills", {}),
                "resume_only_skills": gap_analysis.get("resume_only_skills", {}),
                "similarity_threshold": gap_analysis.get("similarity_threshold"),
            },
            "llm_output": learning_resources,
        }
        return convert_numpy_to_python(response_data)

    except HTTPException:
        raise  # pass validation errors straight through

    except Exception as exc:
        logger.error("Unexpected error in job_analyzer:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {exc}")

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass
