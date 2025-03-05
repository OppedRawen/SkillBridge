# src/manager.py
from agents.extraction_agent import ExtractionAgent
from agents.recommendation_agent import RecommendationAgent

async def run_multi_agent_flow(input_message):
    """
    Orchestrates the multi-agent interaction asynchronously:
    1. ExtractionAgent extracts skills.
    2. RecommendationAgent generates recommendations.
    """
    extraction_agent = ExtractionAgent()
    recommendation_agent = RecommendationAgent()
    
    print("=== Running Extraction Agent ===")
    extraction_response = await extraction_agent.generate_reply(input_message)
    print("Extraction Agent Output:")
    print(extraction_response)
    
    print("=== Running Recommendation Agent ===")
    recommendation_response = await recommendation_agent.generate_reply(extraction_response)
    print("Recommendation Agent Output:")
    print(recommendation_response)
    
    return recommendation_response
