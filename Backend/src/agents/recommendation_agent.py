# src/agents/recommendation_agent.py
from autogen import AssistantAgent  # or the appropriate base class

class RecommendationAgent(AssistantAgent):
    """
    This agent uses ChatGPT to generate learning resource recommendations.
    """
    async def generate_reply(self, extraction_response):
        print("RecommendationAgent.generate_reply() called with:")
        print(extraction_response)
        
        missing_skills = extraction_response.get("resume_analysis", {}).get("missing_skills", [])
        weighted_skills = extraction_response.get("weighted_job_skills", {})
        sorted_skills = sorted(weighted_skills.items(), key=lambda x: x[1], reverse=True)
        
        top_3_jd_skills = [skill for skill, w in sorted_skills[:3]]
        relevant_skills = list(set(missing_skills).union(set(top_3_jd_skills)))
        
        prompt_for_llm = (
            f"Skills to provide recommendations for: {relevant_skills}.\n"
            "Please list some courses, documentation links, or tutorials for each skill. "
            "Ensure the recommendations are concise and practical."
        )
        print("RecommendationAgent prompt to LLM:")
        print(prompt_for_llm)
        
        # Await the LLM call
        llm_response = await self.run_llm(prompt_for_llm)
        print("LLM response:")
        print(llm_response)
        
        return str(llm_response)
