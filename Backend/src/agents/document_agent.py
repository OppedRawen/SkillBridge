from utils.pdf_utils import extract_text_from_pdf

def register_document_agent_functions(user_proxy):
    """
    Register document processing functions with the UserProxyAgent.
    
    Args:
        user_proxy: AutoGen UserProxyAgent
    """
    function_map = {
        "process_resume": process_resume,
        "process_job_description": process_job_description
    }
    
    user_proxy.register_function(function_map=function_map)

def process_resume(pdf_file):
    """
    Process a resume PDF and extract its text content.
    
    Args:
        pdf_file: The uploaded PDF file
        
    Returns:
        str: Extracted text from the resume
    """
    resume_text = extract_text_from_pdf(pdf_file)
    return resume_text

def process_job_description(job_desc_text):
    """
    Process job description text.
    
    Args:
        job_desc_text (str): The job description text
        
    Returns:
        str: Processed job description text
    """
    # For now, just return the text as is
    # Could add preprocessing if needed in the future
    return job_desc_text