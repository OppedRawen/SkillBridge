from extraction.skill_extractor import load_skill_dictionary, extract_skills_from_text

resume_text = """
John Doe
Software Engineer with experience in Python and Java.
Worked on AWS deployments, Docker containers, 
and used machine learning frameworks like TensorFlow.
"""

# 1. Load the skill list
skill_list = load_skill_dictionary()

# 2. Extract skills from the resume text
resume_skills = extract_skills_from_text(resume_text, skill_list)
print("Skills found in resume:", resume_skills)
