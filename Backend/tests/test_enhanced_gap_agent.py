"""
Tests for agents/enhanced_gap_agent.py — semantic skill-gap matching.

The sentence-transformer model is never loaded here: EmbeddingService is
replaced with FakeEmbeddingService which assigns each unique skill text a
distinct one-hot unit vector.

Same text  → cosine similarity 1.0  → matched (above 0.7 threshold)
Diff texts → cosine similarity 0.0  → missing  (below 0.7 threshold)

This lets us test every branch of the matching logic without network
access or GPU/CPU model inference.
"""
import numpy as np
import pytest
from unittest.mock import patch

from agents.enhanced_gap_agent import EnhancedGapAnalyzer

# ---------------------------------------------------------------------------
# Fake embedding service
# ---------------------------------------------------------------------------

class FakeEmbeddingService:
    """
    Deterministic stand-in for EmbeddingService.

    Each unique string is assigned a unique dimension index the first time
    it is seen. Its embedding is the unit vector in that dimension.
    Identical strings → same vector → cosine sim 1.0.
    Different strings → orthogonal vectors → cosine sim 0.0.

    Using DIM=1024 ensures up to 1024 distinct skill texts without collision.
    """
    DIM = 1024

    def __init__(self):
        self._registry: dict[str, int] = {}

    def _vec(self, text: str) -> np.ndarray:
        if text not in self._registry:
            idx = len(self._registry) % self.DIM
            self._registry[text] = idx
        v = np.zeros(self.DIM)
        v[self._registry[text]] = 1.0
        return v

    def get_embedding(self, text: str) -> np.ndarray:
        return self._vec(text)

    def get_embeddings(self, texts: list) -> np.ndarray:
        return np.array([self._vec(t) for t in texts])

    def calculate_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def analyzer() -> EnhancedGapAnalyzer:
    """EnhancedGapAnalyzer with FakeEmbeddingService injected."""
    fake = FakeEmbeddingService()
    with patch("agents.enhanced_gap_agent.EmbeddingService", return_value=fake):
        inst = EnhancedGapAnalyzer(similarity_threshold=0.7)
    return inst


# ---------------------------------------------------------------------------
# Core matching behaviour
# ---------------------------------------------------------------------------

class TestSemanticMatching:
    def test_identical_skill_is_matched(self, analyzer):
        result = analyzer.identify_semantic_skill_gaps(
            job_skills={"python": 3.0},
            resume_skills={"python": 1.0},
        )
        assert "python" in result["matching_skills"]
        assert result["missing_skills"] == {}

    def test_different_skills_marked_missing(self, analyzer):
        # "python" and "java" get orthogonal vectors → sim 0.0 < 0.7
        result = analyzer.identify_semantic_skill_gaps(
            job_skills={"python": 3.0},
            resume_skills={"java": 1.0},
        )
        assert "python" in result["missing_skills"]
        assert result["matching_skills"] == {}

    def test_match_record_contains_expected_fields(self, analyzer):
        result = analyzer.identify_semantic_skill_gaps(
            job_skills={"python": 3.0},
            resume_skills={"python": 1.0},
        )
        m = result["matching_skills"]["python"]
        assert m["job_weight"] == pytest.approx(3.0)
        assert m["resume_match"] == "python"
        assert m["similarity_score"] == pytest.approx(1.0, abs=1e-6)
        assert m["resume_weight"] == pytest.approx(1.0)

    def test_similarity_score_is_python_float_not_numpy(self, analyzer):
        result = analyzer.identify_semantic_skill_gaps(
            job_skills={"python": 3.0},
            resume_skills={"python": 1.0},
        )
        score = result["matching_skills"]["python"]["similarity_score"]
        assert isinstance(score, float), f"Expected float, got {type(score)}"

    def test_unmatched_resume_skill_goes_to_resume_only(self, analyzer):
        result = analyzer.identify_semantic_skill_gaps(
            job_skills={"python": 3.0},
            resume_skills={"python": 1.0, "perl": 1.0},
        )
        assert "perl" in result["resume_only_skills"]
        assert "python" not in result["resume_only_skills"]


# ---------------------------------------------------------------------------
# Sorting guarantee
# ---------------------------------------------------------------------------

class TestMissingSortOrder:
    def test_missing_skills_sorted_descending_by_weight(self, analyzer):
        result = analyzer.identify_semantic_skill_gaps(
            job_skills={"docker": 1.0, "aws": 3.0, "kubernetes": 2.0},
            resume_skills={},
        )
        weights = list(result["missing_skills"].values())
        assert weights == sorted(weights, reverse=True), (
            f"Missing skills not sorted: {result['missing_skills']}"
        )

    def test_missing_keys_are_first_three_in_weight_order(self, analyzer):
        result = analyzer.identify_semantic_skill_gaps(
            job_skills={"c": 1.0, "a": 3.0, "b": 2.0},
            resume_skills={},
        )
        assert list(result["missing_skills"].keys()) == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# Edge / degenerate inputs
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_job_skills_returns_all_resume_only(self, analyzer):
        result = analyzer.identify_semantic_skill_gaps(
            job_skills={},
            resume_skills={"python": 1.0, "sql": 1.0},
        )
        assert result["missing_skills"] == {}
        assert result["matching_skills"] == {}
        assert set(result["resume_only_skills"]) == {"python", "sql"}

    def test_empty_resume_marks_all_as_missing(self, analyzer):
        result = analyzer.identify_semantic_skill_gaps(
            job_skills={"python": 3.0, "sql": 2.0},
            resume_skills={},
        )
        assert set(result["missing_skills"]) == {"python", "sql"}
        assert result["matching_skills"] == {}
        assert result["resume_only_skills"] == {}

    def test_both_empty(self, analyzer):
        result = analyzer.identify_semantic_skill_gaps({}, {})
        assert result["missing_skills"] == {}
        assert result["matching_skills"] == {}
        assert result["resume_only_skills"] == {}

    def test_none_job_skills_treated_as_empty(self, analyzer):
        result = analyzer.identify_semantic_skill_gaps(None, {"python": 1.0})
        assert result["missing_skills"] == {}
        assert "python" in result["resume_only_skills"]

    def test_none_resume_skills_treated_as_empty(self, analyzer):
        result = analyzer.identify_semantic_skill_gaps({"python": 3.0}, None)
        assert "python" in result["missing_skills"]

    def test_result_always_has_required_keys(self, analyzer):
        result = analyzer.identify_semantic_skill_gaps({}, {})
        assert set(result.keys()) == {
            "missing_skills",
            "matching_skills",
            "resume_only_skills",
            "similarity_threshold",
        }

    def test_similarity_threshold_value_in_result(self, analyzer):
        result = analyzer.identify_semantic_skill_gaps({}, {})
        assert result["similarity_threshold"] == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# Embedding failure resilience
# ---------------------------------------------------------------------------

class TestEmbeddingFailureResilience:
    """Verify the analyzer doesn't crash when embeddings come back empty."""

    def test_empty_embedding_array_falls_back_to_zero_vectors(self, analyzer):
        """If get_embeddings returns empty array, should fall back gracefully."""
        analyzer.embedding_service.get_embeddings = lambda texts: np.array([])
        # calculate_similarity of two zero vectors returns 0.0 (our impl handles it)
        analyzer.embedding_service.calculate_similarity = lambda a, b: 0.0

        result = analyzer.identify_semantic_skill_gaps(
            job_skills={"python": 3.0},
            resume_skills={"python": 1.0},
        )
        # With zero vectors, similarity is 0 < 0.7 → python should be missing
        assert "python" in result["missing_skills"]
        # Should not raise


# ---------------------------------------------------------------------------
# Multiple skills — one resume skill matched by best-scoring job skill
# ---------------------------------------------------------------------------

class TestMultiSkillMatching:
    def test_multiple_matches_found(self, analyzer):
        result = analyzer.identify_semantic_skill_gaps(
            job_skills={"python": 3.0, "sql": 2.0, "docker": 1.0},
            resume_skills={"python": 1.0, "sql": 1.0, "docker": 1.0},
        )
        assert set(result["matching_skills"]) == {"python", "sql", "docker"}
        assert result["missing_skills"] == {}

    def test_mixed_match_and_miss(self, analyzer):
        result = analyzer.identify_semantic_skill_gaps(
            job_skills={"python": 3.0, "kubernetes": 2.0},
            resume_skills={"python": 1.0},
        )
        assert "python" in result["matching_skills"]
        assert "kubernetes" in result["missing_skills"]
