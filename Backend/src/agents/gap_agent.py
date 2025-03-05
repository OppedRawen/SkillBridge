import logging

# Configure logging
logger = logging.getLogger(__name__)

def register_gap_agent_functions(user_proxy):
    """
    Register gap analysis functions with the UserProxyAgent.
    
    Args:
        user_proxy: AutoGen UserProxyAgent
    """
    function_map = {
        "identify_skill_gaps": identify_skill_gaps
    }
    
    user_proxy.register_function(function_map=function_map)

def identify_skill_gaps(job_skills, resume_skills):
    """
    Identify skill gaps between job requirements and resume.
    
    Args:
        job_skills (dict): Skills required by the job with weights
        resume_skills (dict): Skills found in the resume
        
    Returns:
        dict: Dictionary containing:
            - missing_skills: Skills in job but not in resume with weights
            - matching_skills: Skills that match between job and resume
            - resume_only_skills: Skills in resume but not required by job
    """
    # Add debug logging
    logger.debug(f"Job skills: {job_skills}")
    logger.debug(f"Resume skills: {resume_skills}")
    
    # Input validation
    if not isinstance(job_skills, dict):
        logger.error(f"job_skills is not a dictionary: {type(job_skills)}")
        job_skills = {}
    
    if not isinstance(resume_skills, dict):
        logger.error(f"resume_skills is not a dictionary: {type(resume_skills)}")
        resume_skills = {}
    
    # Initialize results
    missing_skills = {}
    matching_skills = {}
    resume_only_skills = {}
    
    # Find missing and matching skills
    for skill, weight in job_skills.items():
        if skill in resume_skills:
            matching_skills[skill] = {
                "job_weight": weight,
                "resume_weight": resume_skills[skill]
            }
        else:
            missing_skills[skill] = weight
    
    # Find skills in resume not in job description
    for skill, weight in resume_skills.items():
        if skill not in job_skills:
            resume_only_skills[skill] = weight
            
    # Sort missing skills by weight (importance)
    sorted_missing_skills = dict(sorted(
        missing_skills.items(), 
        key=lambda item: item[1], 
        reverse=True
    ))
    
    result = {
        "missing_skills": sorted_missing_skills,
        "matching_skills": matching_skills,
        "resume_only_skills": resume_only_skills
    }
    
    logger.debug(f"Gap analysis result: {result}")
    return result