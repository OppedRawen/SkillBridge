import re
import traceback
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
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize whitespace and encoding before SkillNER annotation."""
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # Replace common bullet/arrow characters that confuse SkillNER's tokeniser
        text = re.sub(r'[•●◦▸▹►◉✓✗✔✖★☆▪▫]', ' ', text)
        # Collapse multiple spaces/tabs on a single line to one space
        text = re.sub(r'[^\S\n]+', ' ', text)
        # Strip each line and drop more than one consecutive blank line
        lines = [line.strip() for line in text.split('\n')]
        text = re.sub(r'\n{3,}', '\n\n', '\n'.join(lines))
        return text.strip()

    def _annotate_sentence(self, sentence: str, threshold: float = 0.8):
        """
        Run SkillNER on a single sentence and return (skill_text, token_indices) pairs.

        SkillNER has a known IndexError when the lemmatized doc tokenizes differently
        from the original cleaned doc (e.g. "3+" → ["3","+"] on re-tokenization).
        Processing one sentence at a time limits each crash to that one sentence.
        """
        annotations = self.skill_extractor.annotate(sentence)
        raw = []
        for fm in annotations["results"]["full_matches"]:
            raw.append((fm["doc_node_value"], fm["doc_node_id"]))
        for ng in annotations["results"]["ngram_scored"]:
            if ng["score"] >= threshold:
                raw.append((ng["doc_node_value"], ng["doc_node_id"]))
        return raw

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

        text = self._normalize_text(text)
        logger.info("Analyzing job description: %d characters", len(text))

        # Split into sentences so a SkillNER IndexError in one sentence
        # doesn't discard results from the entire document.
        sentences = [s.text.strip() for s in self.nlp(text).sents if s.text.strip()]
        skill_weights = {}
        skipped = 0

        for sentence in sentences:
            try:
                raw_skills = self._annotate_sentence(sentence)
            except Exception as e:
                logger.warning(
                    "SkillNER failed on JD sentence (skipping): %r — %s", sentence[:80], e
                )
                skipped += 1
                continue

            sent_doc = self.nlp(sentence)
            for skill_text, token_indices in raw_skills:
                weight = self._compute_skill_weight(sent_doc, token_indices)
                lower_skill = skill_text.lower()
                if lower_skill not in skill_weights:
                    skill_weights[lower_skill] = weight
                else:
                    skill_weights[lower_skill] = max(skill_weights[lower_skill], weight)

        if skipped:
            logger.warning("Skipped %d/%d sentences due to SkillNER errors", skipped, len(sentences))
        logger.info("Analyzed job description and found %d skills", len(skill_weights))
        return skill_weights
    
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
        
        resume_text = self._normalize_text(resume_text)
        logger.info("Analyzing resume text: %d characters", len(resume_text))

        sentences = [s.text.strip() for s in self.nlp(resume_text).sents if s.text.strip()]
        resume_skills = {}
        skipped = 0

        for sentence in sentences:
            try:
                raw_skills = self._annotate_sentence(sentence)
            except Exception as e:
                logger.warning(
                    "SkillNER failed on resume sentence (skipping): %r — %s", sentence[:80], e
                )
                skipped += 1
                continue

            for skill_text, _ in raw_skills:
                skill = skill_text.lower()
                resume_skills[skill] = 1.0

        if skipped:
            logger.warning("Skipped %d/%d sentences due to SkillNER errors", skipped, len(sentences))
        logger.info("Extracted %d skills from resume", len(resume_skills))
        return resume_skills
    
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

        # doc_node_id from SkillNER is usually a list; guard against int or empty
        if isinstance(skill_indices, int):
            skill_indices = [skill_indices]
        if not skill_indices:
            return base_weight

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