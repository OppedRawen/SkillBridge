"""
Tests for agents/gap_agent.py — exact-string skill-gap matching.

These tests are pure Python with no external dependencies (no model
loading, no network calls) and should run in milliseconds.
"""
import pytest
from agents.gap_agent import identify_skill_gaps


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _result(job_skills, resume_skills):
    return identify_skill_gaps(job_skills, resume_skills)


# ---------------------------------------------------------------------------
# Basic correctness
# ---------------------------------------------------------------------------

class TestIdentifySkillGaps:
    def test_all_skills_match(self):
        result = _result(
            job_skills={"python": 3.0, "sql": 2.0},
            resume_skills={"python": 1.0, "sql": 1.0},
        )
        assert result["missing_skills"] == {}
        assert set(result["matching_skills"]) == {"python", "sql"}
        assert result["resume_only_skills"] == {}

    def test_all_skills_missing(self):
        result = _result(
            job_skills={"python": 3.0, "docker": 2.0},
            resume_skills={"java": 1.0},
        )
        assert set(result["missing_skills"]) == {"python", "docker"}
        assert result["matching_skills"] == {}
        assert "java" in result["resume_only_skills"]

    def test_partial_overlap(self):
        result = _result(
            job_skills={"python": 3.0, "aws": 2.0, "docker": 1.0},
            resume_skills={"python": 1.0, "react": 1.0},
        )
        assert "python" in result["matching_skills"]
        assert set(result["missing_skills"]) == {"aws", "docker"}
        assert "react" in result["resume_only_skills"]

    def test_resume_only_skills_identified(self):
        result = _result(
            job_skills={"python": 3.0},
            resume_skills={"python": 1.0, "perl": 1.0, "cobol": 1.0},
        )
        assert "python" in result["matching_skills"]
        assert set(result["resume_only_skills"]) == {"perl", "cobol"}


# ---------------------------------------------------------------------------
# Sorting guarantee
# ---------------------------------------------------------------------------

class TestMissingSkillsSortOrder:
    def test_missing_sorted_high_to_low_weight(self):
        result = _result(
            job_skills={"docker": 1.0, "aws": 3.0, "kubernetes": 2.0},
            resume_skills={},
        )
        weights = list(result["missing_skills"].values())
        assert weights == sorted(weights, reverse=True)

    def test_missing_skills_preserve_weight_values(self):
        result = _result(
            job_skills={"aws": 3.0, "docker": 1.0},
            resume_skills={},
        )
        assert result["missing_skills"]["aws"] == 3.0
        assert result["missing_skills"]["docker"] == 1.0


# ---------------------------------------------------------------------------
# Matching skill structure
# ---------------------------------------------------------------------------

class TestMatchingSkillStructure:
    def test_match_contains_both_weights(self):
        result = _result({"python": 3.0}, {"python": 1.0})
        match = result["matching_skills"]["python"]
        assert match["job_weight"] == 3.0
        assert match["resume_weight"] == 1.0

    def test_match_only_for_exact_string(self):
        # "Python" != "python" — the extractor lowercases, but the dict
        # keys used here are already lowercase as SkillNER returns them.
        result = _result({"python": 3.0}, {"Python": 1.0})
        assert "python" in result["missing_skills"]
        assert "Python" in result["resume_only_skills"]


# ---------------------------------------------------------------------------
# Empty and degenerate inputs
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_both_empty(self):
        result = _result({}, {})
        assert result == {
            "missing_skills": {},
            "matching_skills": {},
            "resume_only_skills": {},
        }

    def test_empty_job_skills(self):
        result = _result({}, {"python": 1.0})
        assert result["missing_skills"] == {}
        assert result["matching_skills"] == {}
        assert "python" in result["resume_only_skills"]

    def test_empty_resume_skills(self):
        result = _result({"python": 3.0}, {})
        assert "python" in result["missing_skills"]
        assert result["matching_skills"] == {}
        assert result["resume_only_skills"] == {}

    def test_none_job_skills_treated_as_empty(self):
        result = _result(None, {"python": 1.0})
        assert result["missing_skills"] == {}

    def test_none_resume_skills_treated_as_empty(self):
        result = _result({"python": 3.0}, None)
        assert "python" in result["missing_skills"]

    def test_non_dict_job_skills_treated_as_empty(self):
        result = _result(["python", "sql"], {"python": 1.0})
        assert result["missing_skills"] == {}

    def test_non_dict_resume_skills_treated_as_empty(self):
        result = _result({"python": 3.0}, "python sql")
        assert "python" in result["missing_skills"]

    def test_single_skill_match(self):
        result = _result({"python": 1.0}, {"python": 1.0})
        assert "python" in result["matching_skills"]

    def test_large_number_of_skills(self):
        n = 100
        job = {f"skill_{i}": float(i) for i in range(n)}
        resume = {f"skill_{i}": 1.0 for i in range(0, n, 2)}  # every other skill
        result = _result(job, resume)
        assert len(result["matching_skills"]) == n // 2
        assert len(result["missing_skills"]) == n // 2
