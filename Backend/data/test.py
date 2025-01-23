import json

def clean_annotations(input_path, output_path, stop_phrases):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cleaned_data = []
    for entry in data:
        cleaned_annotations = []
        for ann in entry["annotation"]:
            # Check if the 'text' key exists and process only valid annotations
            if "text" in ann:
                if all(phrase.lower() not in ann["text"].lower() for phrase in stop_phrases):
                    cleaned_annotations.append(ann)
            else:
                print(f"Skipped annotation without 'text': {ann}")

        entry["annotation"] = cleaned_annotations
        cleaned_data.append(entry)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_data, f, indent=4)
    print(f"Cleaned annotations saved to {output_path}")

# Define stop phrases
stop_phrases = [
    "less than 1 year", "1 year", "2 years", "additional information",
    "change management", "months", "years",'technical','programming'
]

# Run the cleaning function
clean_annotations("Refined_Skills_Entity_Recognition.json", "cleaned_annotations.json", stop_phrases)
