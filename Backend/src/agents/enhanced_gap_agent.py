import logging
import uuid
from services.embedding_service import EmbeddingService
from services.vector_database import VectorDatabase

# Configure logging
logger = logging.getLogger(__name__)

class EnhancedGapAnalyzer:
    """Enhanced gap analyzer that uses embeddings for semantic matching."""
    
    def __init__(self, similarity_threshold=0.7):
        """
        Initialize the enhanced gap analyzer.
        
        Args:
            similarity_threshold (float): Threshold for considering skills semantically similar
        """
        self.embedding_service = EmbeddingService()
        self.vector_db = VectorDatabase()
        self.similarity_threshold = similarity_threshold
        logger.info(f"Enhanced gap analyzer initialized with similarity threshold: {similarity_threshold}")
    
    def register_functions(self, user_proxy):
        """
        Register functions with the UserProxyAgent.
        
        Args:
            user_proxy: AutoGen UserProxyAgent
        """
        function_map = {
            "identify_semantic_skill_gaps": self.identify_semantic_skill_gaps,
            "find_similar_skills": self.find_similar_skills
        }
        
        user_proxy.register_function(function_map=function_map)
    
    def identify_semantic_skill_gaps(self, job_skills, resume_skills):
        """
        Identify skill gaps using semantic matching.
        
        Args:
            job_skills (dict): Skills required by the job with weights
            resume_skills (dict): Skills found in the resume
            
        Returns:
            dict: Enhanced analysis results
        """
        # Input validation
        if not isinstance(job_skills, dict):
            logger.error(f"job_skills is not a dictionary: {type(job_skills)}")
            job_skills = {}
        
        if not isinstance(resume_skills, dict):
            logger.error(f"resume_skills is not a dictionary: {type(resume_skills)}")
            resume_skills = {}
        
        logger.info(f"Starting semantic gap analysis with {len(job_skills)} job skills and {len(resume_skills)} resume skills")
        
        # Convert dictionaries to lists for processing
        job_skill_texts = list(job_skills.keys())
        resume_skill_texts = list(resume_skills.keys())
        
        # Generate embeddings
        job_embeddings = self._get_or_create_embeddings(job_skill_texts, "job")
        resume_embeddings = self._get_or_create_embeddings(resume_skill_texts, "resume")
        
        # Initialize results
        missing_skills = {}
        matching_skills = {}
        resume_only_skills = {}
        skill_matches = {}
        
        # Find semantic matches for each job skill
        for i, job_skill in enumerate(job_skill_texts):
            job_weight = job_skills[job_skill]
            job_embedding = job_embeddings[i]
            
            # Find best match in resume skills
            best_match = None
            best_score = 0
            
            for j, resume_skill in enumerate(resume_skill_texts):
                resume_embedding = resume_embeddings[j]
                similarity = self.embedding_service.calculate_similarity(job_embedding, resume_embedding)
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = resume_skill
            
            # Determine if there's a semantic match
            if best_match and best_score >= self.similarity_threshold:
                matching_skills[job_skill] = {
                    "job_weight": job_weight,
                    "resume_match": best_match,
                    "similarity_score": best_score,
                    "resume_weight": resume_skills[best_match]
                }
                
                # Track which resume skills are used for matching
                skill_matches[best_match] = skill_matches.get(best_match, []) + [(job_skill, best_score)]
            else:
                missing_skills[job_skill] = job_weight
        
        # Find resume skills that weren't matched to any job skill
        for resume_skill in resume_skill_texts:
            if resume_skill not in skill_matches:
                resume_only_skills[resume_skill] = resume_skills[resume_skill]
        
        # Sort missing skills by weight
        sorted_missing_skills = dict(sorted(
            missing_skills.items(), 
            key=lambda item: item[1], 
            reverse=True
        ))
        
        result = {
            "missing_skills": sorted_missing_skills,
            "matching_skills": matching_skills,
            "resume_only_skills": resume_only_skills,
            "similarity_threshold": self.similarity_threshold
        }
        
        logger.info(f"Semantic gap analysis complete: {len(result['missing_skills'])} missing skills, " +
                  f"{len(result['matching_skills'])} matching skills, {len(result['resume_only_skills'])} resume-only skills")
                  
        return result
    
    def find_similar_skills(self, skill_text, limit=5):
        """
        Find similar skills to the given skill.
        
        Args:
            skill_text (str): The skill to find similar skills for
            limit (int): Maximum number of results
            
        Returns:
            list: List of similar skills with similarity scores
        """
        if not skill_text:
            return []
            
        # Get embedding for the skill
        embedding = self.embedding_service.get_embedding(skill_text)
        if embedding is None:
            return []
        
        # Search for similar skills
        similar_skills = self.vector_db.search_similar_skills(
            embedding, 
            limit=limit,
            threshold=self.similarity_threshold
        )
        
        # Format results
        results = [
            {"skill": skill, "similarity": score, "metadata": metadata}
            for _, skill, score, metadata in similar_skills
        ]
        
        return results
    
    def _get_or_create_embeddings(self, skill_texts, source_type):
        """
        Get embeddings from the database or create new ones.
        
        Args:
            skill_texts (list): List of skill texts
            source_type (str): Type of source ('job' or 'resume')
            
        Returns:
            list: List of embeddings
        """
        embeddings = []
        new_skills = []
        new_texts = []
        
        # Check for existing embeddings in the database
        for skill in skill_texts:
            skill_id = f"{skill}_{source_type}"
            result = self.vector_db.get_skill(skill_id)
            
            if result:
                _, embedding, _ = result
                embeddings.append(embedding)
            else:
                new_skills.append(skill)
                embeddings.append(None)  # Placeholder
        
        # Generate new embeddings if needed
        if new_skills:
            new_embeddings = self.embedding_service.get_embeddings(new_skills)
            
            # Update the database and embeddings list
            for i, skill in enumerate(new_skills):
                skill_id = f"{skill}_{source_type}"
                embedding = new_embeddings[i]
                
                # Add to database
                self.vector_db.add_or_update_skill(
                    skill_id, 
                    skill, 
                    embedding,
                    {"source_type": source_type}
                )
                
                # Find the index in the original list
                original_index = skill_texts.index(skill)
                embeddings[original_index] = embedding
        
        return embeddings