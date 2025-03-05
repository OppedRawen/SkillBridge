import spacy
import logging
from spacy.matcher import PhraseMatcher
from skillNer.general_params import SKILL_DB
from skillNer.skill_extractor_class import SkillExtractor

# Configure logging
logger = logging.getLogger(__name__)

# Load NLP model and skill extractor
try:
    nlp = spacy.load("en_core_web_lg")
    skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)
    logger.info("Successfully loaded SpaCy model and SkillExtractor")
except Exception as e:
    logger.error(f"Error loading NLP model: {str(e)}")
    raise

def analyze_resume(resume_text):
    """
    Extract skills from a resume.
    
    Args:
        resume_text (str): Text content of the resume
        
    Returns:
        dict: Dictionary of skills found in the resume
    """
    if not resume_text or not isinstance(resume_text, str):
        logger.error(f"Invalid resume text: {type(resume_text)}")
        return {}
    
    logger.info(f"Analyzing resume text: {len(resume_text)} characters")
    
    try:
        # Extract annotations using SkillNER
        annotations = skill_extractor.annotate(resume_text)
        
        # Extract skills from annotations with a confidence threshold
        resume_skills = {}
        threshold = 0.8
        
        # Add debug info
        logger.debug(f"Full matches: {len(annotations['results']['full_matches'])}")
        logger.debug(f"NGram matches: {len(annotations['results']['ngram_scored'])}")
        
        # Process full matches (high confidence)
        for match in annotations["results"]["full_matches"]:
            skill = match["doc_node_value"].lower()
            resume_skills[skill] = 1.0  # Base weight for skills from resume
        
        # Process ngram matches above threshold
        for match in annotations["results"]["ngram_scored"]:
            if match["score"] >= threshold:
                skill = match["doc_node_value"].lower()
                resume_skills[skill] = 1.0
        
        logger.info(f"Extracted {len(resume_skills)} skills from resume")
        logger.debug(f"Resume skills: {resume_skills}")
        
        # Return empty dict if no skills found to avoid None
        return resume_skills
        
    except Exception as e:
        logger.error(f"Error analyzing resume: {str(e)}")
        # Return empty dict instead of None
        return {}