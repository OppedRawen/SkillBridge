# src/agents/extraction_agent.py
from autogen import AssistantAgent  # or the appropriate base class
from services.resume_service import analyze_resume_and_job
from services.job_description_analyzer import analyze_job_description

class ExtractionAgent(AssistantAgent):
    """
    This agent extracts skills from the candidate's resume and job description.
    """
    async def generate_reply(self, input_message):
        print("ExtractionAgent.generate_reply() called with:")
        print(input_message)
        
        resume_file = input_message.get("resume_file")
        job_desc_text = input_message.get("job_description")
        
        # Await the asynchronous resume analysis
        extraction_result = await analyze_resume_and_job(resume_file, job_desc_text)
        # Assuming analyze_job_description is synchronous
        weighted_skills = analyze_job_description(job_desc_text)
        
        combined_output = {
            "resume_analysis": extraction_result,
            "weighted_job_skills": weighted_skills
        }
        print("ExtractionAgent returning:")
        print(combined_output)
        return combined_output
