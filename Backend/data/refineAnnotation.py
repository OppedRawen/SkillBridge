import json
import re

# Load the cleaned JSON data
with open("Cleaned_Entity_Recognition.json", "r", encoding="utf-8") as f:
    data = json.load(f)

def refine_skills_annotation(data):
    """
    Breaks down skills chunks into individual skill annotations.
    """
    refined_data = []
    for entry in data:
        content = entry["content"]
        annotations = entry["annotation"]
        new_annotations = []

        for annotation in annotations:
            if "label" not in annotation or not annotation["label"]:
                print("Skipping annotation without label:", annotation)
                continue
            if annotation["label"][0] == "Skills":
                skill_text = annotation["points"][0]["text"]
                start_index = annotation["points"][0]["start"]
                # Extract individual skills using a regex
                skills = re.findall(r"\b[\w\-\+]+(?: [\w\-\+]+)*\b", skill_text)

                for skill in skills:
                    skill_start = content.find(skill, start_index)
                    skill_end = skill_start + len(skill)
                    if skill_start != -1:
                        new_annotations.append({
                            "start": skill_start,
                            "end": skill_end,
                            "label": "Skill",
                            "text": skill
                        })
            else:
                # Retain non-skills annotations as they are
                new_annotations.append(annotation)

        # Update the entry with refined annotations
        refined_data.append({
            "content": content,
            "annotation": new_annotations
        })

    return refined_data

# Refine the skills annotations
refined_annotations = refine_skills_annotation(data)

# Save the refined data to a new JSON file
with open("Refined_Skills_Entity_Recognition.json", "w", encoding="utf-8") as f:
    json.dump(refined_annotations, f, indent=4)

print("Refined annotations saved to Refined_Skills_Entity_Recognition.json")
