import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def get_learning_resources(missing_skills: dict, job_description: str) -> str:
    """
    Generate learning resource recommendations for the top missing skills.

    Calls OpenAI GPT-3.5-turbo when OPENAI_API_KEY is available.
    Returns a plain-text fallback message when the key is absent or the
    API call fails, so the rest of the analysis is always returned to the
    caller regardless.

    Args:
        missing_skills:  {skill_text: weight} sorted high→low — only the
                         top 5 are sent to the model
        job_description: original job description text for context

    Returns:
        str  —  formatted recommendations, or a graceful fallback string
    """
    top_skills = list(missing_skills.keys())[:5]

    if not top_skills:
        return "No skill gaps identified — your resume already matches the job requirements well!"

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set; returning skill list without LLM recommendations")
        return (
            "Skills to develop: " + ", ".join(top_skills) + ".\n\n"
            "Tip: set OPENAI_API_KEY in your .env file to receive personalised course, "
            "book, and project recommendations for each skill."
        )

    prompt = f"""I am applying for a role with the following description:

{job_description}

The skills most missing from my resume are: {", ".join(top_skills)}.

For each skill please provide:
1. One sentence explaining why it matters for this role
2. Two online courses (free or paid) with URLs if possible
3. One book recommendation
4. One small project idea to practise the skill

Keep the response concise and practical."""

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a career coach who gives concise, practical skill-development advice.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1200,
        )
        recommendations = response.choices[0].message.content
        logger.info("OpenAI recommendations retrieved successfully")
        return recommendations

    except Exception as exc:
        logger.error("OpenAI API call failed: %s", exc)
        return (
            f"Learning resources temporarily unavailable ({type(exc).__name__}). "
            f"Skills to develop: {', '.join(top_skills)}."
        )
