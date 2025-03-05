import os
from openai import OpenAI
import logging
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize the OpenAI client with the new SDK format
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def register_resource_agent_functions(user_proxy):
    """
    Register resource recommendation functions with the UserProxyAgent.
    
    Args:
        user_proxy: AutoGen UserProxyAgent
    """
    function_map = {
        "get_learning_resources": get_learning_resources
    }
    
    user_proxy.register_function(function_map=function_map)

def get_learning_resources(missing_skills, job_description):
    """
    Get learning resources for missing skills using ChatGPT.
    
    Args:
        missing_skills (dict): Dictionary of missing skills with weights
        job_description (str): The original job description for context
        
    Returns:
        str: Formatted resource recommendations from ChatGPT
    """
    # Prepare the top missing skills (limit to top 5 for focus)
    top_skills = list(missing_skills.keys())[:5]
    
    if not top_skills:
        return "No skill gaps identified! Your resume already matches the job requirements well."
    
    # Construct prompt for ChatGPT
    prompt = f"""
    I'm applying for a job with the following description:
    
    {job_description}
    
    I need learning resources for these skills that are missing from my resume:
    {', '.join(top_skills)}
    
    For each skill, please provide:
    1. A concise explanation of why this skill is important for the role
    2. Two recommended online courses (free or paid)
    3. One book recommendation
    4. One practical project idea to develop this skill
    
    Format your response in a clear, easy-to-read way. Focus on practical advice.
    """
    
    # Call ChatGPT API using the new client syntax (OpenAI SDK 1.0.0+)
    try:
        logger.info(f"Calling OpenAI API for learning resources on: {', '.join(top_skills)}")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a career coach specializing in skill development and learning resources."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1200
        )
        
        # Extract and return the response content with the new schema
        recommendations = response.choices[0].message.content
        logger.info("Successfully retrieved learning resources from OpenAI")
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting resource recommendations: {str(e)}")
        return f"Error getting resource recommendations: {str(e)}"