import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import tempfile
import os
import traceback
from utils.pdf_utils import extract_text_from_pdf
from services.job_description_analyzer import analyze_job_description
from services.resume_analyzer import analyze_resume
from agents.enhanced_gap_agent import EnhancedGapAnalyzer
from agents.resource_agent import get_learning_resources

# Import agent modules
from agents.agent_config import create_agents
from agents.document_agent import register_document_agent_functions
from agents.skill_agent import register_skill_agent_functions

# Configure logging
logging.basicConfig(level=logging.DEBUG)
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
    job_description: str = Form(...),
    use_semantic: bool = Form(True)
):
    """
    Analyze a job description and resume for skill gaps and provide learning resources.
    
    Args:
        file: The resume PDF file
        job_description: The job description text
        use_semantic: Whether to use semantic matching (vector embeddings) for skill comparison
    """
    temp_path = None
    try:
        logger.info(f"Received job analysis request: file={file.filename}, job desc length={len(job_description)}")
        logger.info(f"Semantic matching enabled: {use_semantic}")
        
        # Step 1: Create agents
        try:
            logger.info("Creating AutoGen agents...")
            user_proxy, document_agent, skill_agent, gap_agent, resource_agent, manager = create_agents()
            logger.info("Agents created successfully")
            
            # Register functions with the user proxy
            register_document_agent_functions(user_proxy)
            register_skill_agent_functions(user_proxy)
            
            # Initialize the enhanced gap analyzer
            enhanced_gap_analyzer = EnhancedGapAnalyzer(similarity_threshold=0.7)
            enhanced_gap_analyzer.register_functions(user_proxy)
            
            logger.info("All functions registered with user proxy")
            
        except Exception as agent_error:
            logger.error(f"Error creating agents: {str(agent_error)}")
            return {
                "status": "error",
                "message": "Failed to initialize agents",
                "error": str(agent_error),
                "llm_output": "Our AI system encountered an initialization error. Please try again later."
            }
        
        # Step 2: Save the uploaded file
        logger.info("Saving temporary file...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(await file.read())
            temp_path = temp_file.name
        logger.info(f"File saved to {temp_path}")
        
        # Step 3: Process the documents
        try:
            logger.info("Processing the resume PDF...")
            # We'll directly use the utilities rather than go through agents for this step
            resume_text = extract_text_from_pdf({"file": open(temp_path, 'rb')})
            if resume_text.startswith("Error"):
                raise ValueError(f"PDF extraction failed: {resume_text}")
                
            logger.info(f"Resume text extracted: {len(resume_text)} characters")
            logger.debug(f"Resume text sample: {resume_text[:200]}...")
            
            # Process job description (just use the text as is)
            processed_job_description = job_description
            logger.info(f"Job description processed: {len(processed_job_description)} characters")
            
            # Extract skills from job description
            logger.info("Extracting skills from job description...")
            job_skills = analyze_job_description(processed_job_description)
            
            if not job_skills:
                logger.warning("No skills found in job description!")
                job_skills = {}  # Ensure it's an empty dict, not None
                
            logger.info(f"Job skills extracted: {len(job_skills)} skills found")
            logger.debug(f"Job skills: {job_skills}")
            
            # Extract skills from resume
            logger.info("Extracting skills from resume...")
            resume_skills = analyze_resume(resume_text)
            
            if not resume_skills:
                logger.warning("No skills found in resume!")
                resume_skills = {}  # Ensure it's an empty dict, not None
                
            logger.info(f"Resume skills extracted: {len(resume_skills)} skills found")
            logger.debug(f"Resume skills: {resume_skills}")
            
            # Step 4: Perform gap analysis (with or without semantic matching)
            logger.info("Performing skill gap analysis...")
            
            if use_semantic:
                # Use semantic matching with vector embeddings
                gap_analysis = enhanced_gap_analyzer.identify_semantic_skill_gaps(
                    job_skills if job_skills else {}, 
                    resume_skills if resume_skills else {}
                )
                analysis_type = "semantic"
            else:
                # Use traditional exact matching
                from agents.gap_agent import identify_skill_gaps
                gap_analysis = identify_skill_gaps(
                    job_skills if job_skills else {}, 
                    resume_skills if resume_skills else {}
                )
                analysis_type = "exact"
                
            if not gap_analysis:
                logger.warning("Gap analysis returned None!")
                # Provide a default structure
                gap_analysis = {
                    "missing_skills": {},
                    "matching_skills": {},
                    "resume_only_skills": {}
                }
                
            logger.info(f"Gap analysis complete: {len(gap_analysis.get('missing_skills', {}))} missing skills identified")
            
            # Step 5: Get learning resources for missing skills
            missing_skills = gap_analysis.get('missing_skills', {})
            if missing_skills:
                logger.info("Getting learning resources for missing skills...")
                learning_resources = get_learning_resources(missing_skills, job_description)
                logger.info("Learning resources retrieved")
            else:
                learning_resources = "No missing skills identified. Your resume already matches the job requirements well!"
            
            # Clean up the temporary file
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
                temp_path = None
            
            # Return the complete analysis
            return {
                "status": "success",
                "file_name": file.filename,
                "analysis_type": analysis_type,
                "analysis": {
                    "job_skills": job_skills if job_skills else {},
                    "resume_skills": resume_skills if resume_skills else {},
                    "matching_skills": gap_analysis.get('matching_skills', {}),
                    "missing_skills": gap_analysis.get('missing_skills', {}),
                    "resume_only_skills": gap_analysis.get('resume_only_skills', {}),
                    "similarity_threshold": gap_analysis.get('similarity_threshold', None)
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
                except:
                    pass
                temp_path = None
                
            return {
                "status": "error",
                "message": "Failed to process documents",
                "error": str(process_error),
                "llm_output": "An error occurred while processing your documents. Please ensure your resume is a valid PDF and try again."
            }
        
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Unexpected error in job_analyzer: {str(e)}\n{error_details}")
        
        # Clean up the temporary file if it exists
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass
            
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.get("/similar-skills/{skill}")
async def find_similar_skills(skill: str, limit: int = 5):
    """
    Find skills similar to the given skill using vector embeddings.
    
    Args:
        skill: The skill to find similar skills for
        limit: Maximum number of results to return
    """
    try:
        gap_analyzer = EnhancedGapAnalyzer()
        similar_skills = gap_analyzer.find_similar_skills(skill, limit)
        
        return {
            "status": "success",
            "skill": skill,
            "similar_skills": similar_skills
        }
    except Exception as e:
        logger.error(f"Error finding similar skills: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to find similar skills: {str(e)}")