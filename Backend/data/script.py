

import json
import os
import re
import pandas as pd
import concurrent.futures
from tqdm import tqdm
def load_skill_dictionary(dictionary_path="new_skills.json"):
    """
    Loads the skill dictionary from JSON and returns:
    alias_to_skill: a dict mapping skill aliases to a canonical skill name.
    """
    with open(dictionary_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    alias_to_skill = {}
    for entry in data["skills"]:
        main_skill = entry["name"]
        # Include the main skill as an alias to itself
        alias_to_skill[main_skill.lower()] = main_skill

        # Include synonyms
        for syn in entry.get("synonyms", []):
            alias_to_skill[syn.lower()] = main_skill

    return alias_to_skill
alias_map = load_skill_dictionary(dictionary_path = "new_skills.json")
def auto_label_text(text: str, alias_map: dict):
    entities = []
    lower_text = text.lower()
    for alias, canonical_skill in alias_map.items():
        pattern = rf"\b{re.escape(alias)}\b"
        for match in re.finditer(pattern, lower_text, flags=re.IGNORECASE):
            start, end = match.start(), match.end()
            entities.append((start, end, "SKILL"))
    entities.sort(key=lambda x: x[0])
    return entities
def label_one_text(text: str, alias_map: dict):
    ents = auto_label_text(text, alias_map)
    return {
        "text": text,
        "ents": [{"start": s, "end": e, "label": lbl} for (s, e, lbl) in ents]
    }
def parallel_annotate(job_texts, alias_map, max_workers=4):
    from tqdm import tqdm  # for progress bar

    labeled_docs = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # We pass 'alias_map' as an argument so each process can see it
        futures = [executor.submit(label_one_text, txt, alias_map) for txt in job_texts]

        for future in tqdm(
            concurrent.futures.as_completed(futures), 
            total=len(futures), 
            desc="Annotating"
        ):
            result = future.result()  # might raise if a worker crashed
            labeled_docs.append(result)

    return labeled_docs
if __name__ == "__main__":

    alias_map = load_skill_dictionary("new_skills.json")
    df_jobs = pd.read_csv("job_title_des.csv")
    job_texts = df_jobs["Job Description"].dropna().tolist()

    # Actually do parallel annotation
    labeled_docs = parallel_annotate(job_texts, alias_map, 8)

    with open("auto_labeled_output.json", "w", encoding="utf-8") as f:
        json.dump(labeled_docs, f, indent=2)

    print("Done annotating!")