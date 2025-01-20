# 1. Imports
import spacy
from spacy.matcher import PhraseMatcher

# SkillNer imports
from skillNer.general_params import SKILL_DB
from skillNer.skill_extractor_class import SkillExtractor

# 2. Load the SpaCy language model
nlp = spacy.load("en_core_web_lg")

# 3. Initialize SkillExtractor with default skill DB and PhraseMatcher
skill_extractor = SkillExtractor(
    nlp,
    SKILL_DB,  # default EMSI-based skill database
    PhraseMatcher
)

# 4. Your text to analyze
job_description = """
You are a Python developer with a solid experience in web development
and can manage projects. You quickly adapt to new environments
and speak fluently English and French
"""

# 5. Extract skills
annotations = skill_extractor.annotate(job_description)

# 6. Analyze or print the results
print(annotations)
