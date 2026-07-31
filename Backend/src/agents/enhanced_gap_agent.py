import logging
import numpy as np
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

_ZERO_VEC_DIM = 384  # dimension of all-MiniLM-L6-v2


class EnhancedGapAnalyzer:
    """Semantic skill-gap analyzer using sentence embeddings and cosine similarity."""

    def __init__(self, similarity_threshold: float = 0.7):
        self.embedding_service = EmbeddingService()
        self.similarity_threshold = similarity_threshold
        logger.info("EnhancedGapAnalyzer ready (threshold=%.2f)", similarity_threshold)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def identify_semantic_skill_gaps(
        self, job_skills: dict, resume_skills: dict
    ) -> dict:
        """
        Compare job and resume skills using vector-embedding cosine similarity.

        Args:
            job_skills:    {skill_text: weight}  extracted from job description
            resume_skills: {skill_text: weight}  extracted from resume

        Returns:
            {
              "missing_skills":     {skill: weight},  sorted high→low weight
              "matching_skills":    {skill: {job_weight, resume_match,
                                            similarity_score, resume_weight}},
              "resume_only_skills": {skill: weight},
              "similarity_threshold": float,
            }
        """
        if not isinstance(job_skills, dict):
            logger.error("job_skills must be dict, got %s — treating as empty", type(job_skills))
            job_skills = {}
        if not isinstance(resume_skills, dict):
            logger.error("resume_skills must be dict, got %s — treating as empty", type(resume_skills))
            resume_skills = {}

        job_texts = list(job_skills.keys())
        resume_texts = list(resume_skills.keys())

        logger.info(
            "Semantic gap analysis: %d job skills vs %d resume skills",
            len(job_texts), len(resume_texts),
        )

        # Fast path — nothing in the job description
        if not job_texts:
            return {
                "missing_skills": {},
                "matching_skills": {},
                "resume_only_skills": dict(resume_skills),
                "similarity_threshold": self.similarity_threshold,
            }

        job_embeddings = self._get_embeddings(job_texts)
        resume_embeddings = self._get_embeddings(resume_texts) if resume_texts else []

        missing_skills: dict = {}
        matching_skills: dict = {}
        matched_resume_skills: set = set()

        for i, job_skill in enumerate(job_texts):
            job_emb = job_embeddings[i] if i < len(job_embeddings) else np.zeros(_ZERO_VEC_DIM)
            job_weight = job_skills[job_skill]

            best_resume_skill = None
            best_score = 0.0

            for j, resume_skill in enumerate(resume_texts):
                if j >= len(resume_embeddings):
                    continue
                score = self.embedding_service.calculate_similarity(job_emb, resume_embeddings[j])
                if score > best_score:
                    best_score = score
                    best_resume_skill = resume_skill

            if best_resume_skill is not None and best_score >= self.similarity_threshold:
                matching_skills[job_skill] = {
                    "job_weight": job_weight,
                    "resume_match": best_resume_skill,
                    "similarity_score": float(best_score),
                    "resume_weight": resume_skills[best_resume_skill],
                }
                matched_resume_skills.add(best_resume_skill)
            else:
                missing_skills[job_skill] = job_weight

        resume_only_skills = {
            skill: resume_skills[skill]
            for skill in resume_texts
            if skill not in matched_resume_skills
        }

        sorted_missing = dict(
            sorted(missing_skills.items(), key=lambda kv: kv[1], reverse=True)
        )

        logger.info(
            "Done: %d missing, %d matched, %d resume-only",
            len(sorted_missing), len(matching_skills), len(resume_only_skills),
        )

        return {
            "missing_skills": sorted_missing,
            "matching_skills": matching_skills,
            "resume_only_skills": resume_only_skills,
            "similarity_threshold": self.similarity_threshold,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_embeddings(self, skill_texts: list) -> list:
        """
        Return a list of numpy embedding arrays, one per skill text.
        Falls back to zero vectors on encoding failure so the caller never
        receives None values.
        """
        if not skill_texts:
            return []

        embeddings = self.embedding_service.get_embeddings(skill_texts)

        # get_embeddings returns np.array([]) on total failure
        if embeddings is None or len(embeddings) == 0:
            logger.warning(
                "Embedding generation failed for %d skills; substituting zero vectors",
                len(skill_texts),
            )
            return [np.zeros(_ZERO_VEC_DIM) for _ in skill_texts]

        result = list(embeddings)

        # Pad if the encoder silently dropped some inputs
        if len(result) < len(skill_texts):
            shortfall = len(skill_texts) - len(result)
            logger.warning("Got %d embeddings for %d skills; padding %d with zeros",
                           len(result), len(skill_texts), shortfall)
            result.extend([np.zeros(_ZERO_VEC_DIM)] * shortfall)

        return result
