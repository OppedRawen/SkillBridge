import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import tempfile
import os
import traceback
from utils.pdf_utils import extract_text_from_pdf
from services.job_description_analyzer import analyze_job_description
from services.resume_analyzer import analyze_resume
from agents.gap_agent import identify_skill_gaps
from agents.resource_agent import get_learning_resources

# Import agent modules
from agents.agent_config import create_agents
from agents.document_agent import register_document_agent_functions
from agents.skill_agent import register_skill_agent_functions
from agents.gap_agent import register_gap_agent_functions
from agents.resource_agent import register_resource_agent_functions

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    responses={404: {"description": "Not found"}},
)

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify the API is working."""
    return {"message": "Jobs API is working!"}

@router.post("/jobAnalyzer")
async def job_analyzer(
    file: UploadFile = File(...),
    job_description: str = Form(...)
):
    """
    Analyze a job description and resume for skill gaps and provide learning resources.
    
    Args:
        file: The resume PDF file
        job_description: The job description text
    """
    temp_path = None
    try:
        logger.info(f"Received job analysis request: file={file.filename}, job desc length={len(job_description)}")
        
        # Step 1: Create agents
        try:
            logger.info("Creating AutoGen agents...")
            user_proxy, document_agent, skill_agent, gap_agent, resource_agent, manager = create_agents()
            logger.info("Agents created successfully")
            
            # Register functions with the user proxy
            register_document_agent_functions(user_proxy)
            register_skill_agent_functions(user_proxy)
            register_gap_agent_functions(user_proxy)
            register_resource_agent_functions(user_proxy)
            logger.info("All functions registered with user proxy")
            
        except Exception as agent_error:
            logger.error(f"Error creating agents: {str(agent_error)}")
            return {
                "status": "error",
                "message": "Failed to initialize agents",
                "error": str(agent_error),
                "llm_output": "Our AI system encountered an initialization error. Please try again later."
            }
        
        # Step 2: Process the documents
        try:
            logger.info("Processing the resume PDF...")
            # Read the file content
            file_content = await file.read()
            
            # Save to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name
            
            logger.info(f"Saved resume to temporary file: {temp_path}")
            
            # Extract text from the PDF file path directly
            resume_text = extract_text_from_pdf(temp_path)
            logger.info(f"Resume text extracted: {len(resume_text)} characters")
            
            # Process job description (just use the text as is)
            processed_job_description = job_description
            logger.info(f"Job description processed: {len(processed_job_description)} characters")
            
            # Extract skills from job description
            logger.info("Extracting skills from job description...")
            job_skills = analyze_job_description(processed_job_description)
            logger.info(f"Job skills extracted: {len(job_skills)} skills found")
            
            # Extract skills from resume
            logger.info("Extracting skills from resume...")
            resume_skills = analyze_resume(resume_text)
            logger.info(f"Resume skills extracted: {len(resume_skills)} skills found")
            
            # Step 3: Perform gap analysis
            logger.info("Performing skill gap analysis...")
            gap_analysis = identify_skill_gaps(job_skills, resume_skills)
            logger.info(f"Gap analysis complete: {len(gap_analysis['missing_skills'])} missing skills identified")
            
            # Step 4: Get learning resources for missing skills
            if gap_analysis['missing_skills']:
                logger.info("Getting learning resources for missing skills...")
                learning_resources = get_learning_resources(gap_analysis['missing_skills'], job_description)
                logger.info("Learning resources retrieved")
            else:
                learning_resources = "No missing skills identified. Your resume already matches the job requirements well!"
            
            # Clean up the temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    temp_path = None
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file: {str(e)}")
            
            # Return the complete analysis
            return {
                "status": "success",
                "file_name": file.filename,
                "analysis": {
                    "job_skills": job_skills,
                    "resume_skills": resume_skills,
                    "matching_skills": gap_analysis['matching_skills'],
                    "missing_skills": gap_analysis['missing_skills'],
                    "resume_only_skills": gap_analysis['resume_only_skills']
                },
                "llm_output": learning_resources
            }
            
        except Exception as process_error:
            logger.error(f"Error processing documents: {str(process_error)}")
            logger.error(traceback.format_exc())
            
            # Clean up the temporary file if it exists
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    temp_path = None
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file: {str(e)}")
                
            return {
                "status": "error",
                "message": "Failed to process documents",
                "error": str(process_error),
                "llm_output": "An error occurred while processing your documents. Please try again."
            }
        
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Unexpected error in job_analyzer: {str(e)}\n{error_details}")
        
        # Clean up the temporary file if it exists
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete temporary file during error handling: {str(cleanup_error)}")
            
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")