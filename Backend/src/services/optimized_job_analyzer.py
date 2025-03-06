import spacy
import logging
from spacy.matcher import PhraseMatcher
from skillNer.general_params import SKILL_DB
from skillNer.skill_extractor_class import SkillExtractor

# Configure logging
logger = logging.getLogger(__name__)

class SkillExtractorSingleton:
    """
    Singleton class to ensure NLP model and skill extractor are loaded only once.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            logger.info("Creating new SkillExtractorSingleton instance")
            cls._instance = super(SkillExtractorSingleton, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance
    
    def initialize(self):
        """Load the NLP model and initialize the skill extractor once."""
        logger.info("Loading SpaCy model and SkillNER extractors...")
        self.nlp = spacy.load("en_core_web_lg")
        self.skill_extractor = SkillExtractor(self.nlp, SKILL_DB, PhraseMatcher)
        logger.info("SpaCy model and SkillNER extractors loaded successfully")
    
    def analyze_job_description(self, text):
        """
        Extract and weight skills from job description text.
        
        Args:
            text (str): Job description text
            
        Returns:
            dict: Dictionary of skills with weights
        """
        if not text:
            logger.warning("Empty job description text provided")
            return {}
            
        logger.info(f"Analyzing job description: {len(text)} characters")
        
        try:
            # Extract annotations
            annotations = self.skill_extractor.annotate(text)
            
            # Combine full_matches & ngram_scored
            raw_skills = []  # store (skill_text, token_indices)
            threshold = 0.8
            
            for fm in annotations["results"]["full_matches"]:
                raw_skills.append((fm["doc_node_value"], fm["doc_node_id"]))
            
            for ng in annotations["results"]["ngram_scored"]:
                if ng["score"] >= threshold:
                    raw_skills.append((ng["doc_node_value"], ng["doc_node_id"]))
            
            logger.debug(f"Extracted {len(raw_skills)} raw skills")
            
            # Convert text to SpaCy doc for context analysis
            doc = self.nlp(text)
            
            # Calculate weights & aggregate
            skill_weights = {}
            for skill_text, token_indices in raw_skills:
                weight = self._compute_skill_weight(doc, token_indices)
                lower_skill = skill_text.lower()
                
                # If skill is repeated, take the max weight
                if lower_skill not in skill_weights:
                    skill_weights[lower_skill] = weight
                else:
                    skill_weights[lower_skill] = max(skill_weights[lower_skill], weight)
            
            logger.info(f"Analyzed job description and found {len(skill_weights)} skills")
            return skill_weights
            
        except Exception as e:
            logger.error(f"Error analyzing job description: {str(e)}")
            return {}
    
    def analyze_resume(self, resume_text):
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
            annotations = self.skill_extractor.annotate(resume_text)
            
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
            
            return resume_skills
            
        except Exception as e:
            logger.error(f"Error analyzing resume: {str(e)}")
            # Return empty dict instead of None
            return {}
    
    def _compute_skill_weight(self, doc, skill_indices):
        """
        Compute skill weight based on surrounding context.
        
        Args:
            doc: SpaCy document
            skill_indices: Indices of the skill tokens
            
        Returns:
            float: Computed weight
        """
        keywords_required = {
            "must", "required", "mandatory", "essential", "needed",
            "necessity", "expertise", "strong", "proficiency"
        }
        
        keywords_preferred = {
            "preferred", "nice-to-have", "plus", "beneficial", 
            "bonus", "familiarity", "desire"
        }
        
        base_weight = 1.0
        window_size = 5  # how many tokens to look around
        
        start_token = min(skill_indices)
        end_token = max(skill_indices)
        
        # Build context range
        left_context_start = max(0, start_token - window_size)
        right_context_end = min(len(doc), end_token + window_size + 1)
        
        surrounding_tokens = [t.lower_ for t in doc[left_context_start:right_context_end]]
        
        # If 'must' or 'required' is near, increase weight
        if any(k in surrounding_tokens for k in keywords_required):
            base_weight += 2.0
            
        # If 'preferred' is near, increase weight slightly
        if any(k in surrounding_tokens for k in keywords_preferred):
            base_weight += 1.0
            
        return base_weight

# Create a global instance of the skill extractor singleton
skill_extractor_instance = SkillExtractorSingleton()

# Public API functions that use the singleton
def analyze_job_description(text):
    """
    Public function to analyze job description text.
    
    Args:
        text (str): Job description text
        
    Returns:
        dict: Dictionary of skills with weights
    """
    return skill_extractor_instance.analyze_job_description(text)

def analyze_resume(text):
    """
    Public function to analyze resume text.
    
    Args:
        text (str): Resume text
        
    Returns:
        dict: Dictionary of skills found in the resume
    """
    return skill_extractor_instance.analyze_resume(text)