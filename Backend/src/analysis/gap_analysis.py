def analyze_skill_gap(resume_skills: set, job_skills: set) -> dict:
    """
    Compare skills from the résumé and job description to identify matches and gaps.

    Args:
        resume_skills (set): Skills found in the résumé.
        job_skills (set): Skills required in the job description.

    Returns:
        dict: A dictionary with matched and missing skills.
    """
    # Find the overlap (skills that match)
    matched_skills = resume_skills.intersection(job_skills)

    # Find the missing skills (required by the job but not in the resume)
    missing_skills = job_skills.difference(resume_skills)

    # Return the analysis as a dictionary
    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills
    }
