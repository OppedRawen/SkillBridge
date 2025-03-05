from services.job_description_analyzer import analyze_job_description
from services.resume_analyzer import analyze_resume

def register_skill_agent_functions(user_proxy):
    """
    Register skill extraction functions with the UserProxyAgent.
    
    Args:
        user_proxy: AutoGen UserProxyAgent
    """
    function_map = {
        "extract_job_skills": extract_job_skills,
        "extract_resume_skills": extract_resume_skills
    }
    
    user_proxy.register_function(function_map=function_map)

def extract_job_skills(job_description_text):
    """
    Extract skills from a job description.
    
    Args:
        job_description_text (str): The job description text
        
    Returns:
        dict: Dictionary of skills with weights
    """
    return analyze_job_description(job_description_text)

def extract_resume_skills(resume_text):
    """
    Extract skills from a resume.
    
    Args:
        resume_text (str): The processed resume text
        
    Returns:
        dict: Dictionary of skills found in the resume
    """
    return analyze_resume(resume_text)