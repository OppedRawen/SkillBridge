import spacy
from spacy.training.example import Example
import json
import random
from pathlib import Path
from tqdm import tqdm  # Progress bar

# Start with a blank English model
nlp = spacy.blank("en")
print("Initialized a blank English model.")

# Add the NER pipeline
if "ner" not in nlp.pipe_names:
    ner = nlp.add_pipe("ner")
else:
    ner = nlp.get_pipe("ner")

# Load and preprocess the dataset
with open("Cleaned_Entity_Recognition.json", "r", encoding="utf-8") as f:
    kaggle_data = json.load(f)

def preprocess_data(data):
    cleaned_data = []
    for item in data:
        text = item["content"]
        entities = []

        for annotation in item["annotation"]:
            if (
                "points" in annotation and annotation["points"]
                and "label" in annotation and annotation["label"]
            ):
                start = annotation["points"][0]["start"]
                end = annotation["points"][0]["end"]
                label = annotation["label"][0]

                # Ensure no leading/trailing spaces
                if text[start:end].strip() != text[start:end]:
                    print(f"Skipped entity with leading/trailing spaces: {text[start:end]}")
                    continue

                entities.append((start, end, label))
                ner.add_label(label)  # Add label to the pipeline

        if entities:
            cleaned_data.append((text, {"entities": entities}))

    return cleaned_data

training_data = preprocess_data(kaggle_data)
print(f"Prepared {len(training_data)} training examples.")

# Fine-tune the model
def train_ner(nlp, training_data, output_dir, n_iter=20):
    optimizer = nlp.begin_training()
    for iteration in tqdm(range(n_iter), desc="Training Progress"):
        random.shuffle(training_data)
        losses = {}
        for text, annotations in training_data:
            try:
                doc = nlp.make_doc(text)
                example = Example.from_dict(doc, annotations)
                nlp.update([example], drop=0.5, losses=losses)
            except Exception as e:
                print(f"Skipped invalid example: {e}")
        print(f"Iteration {iteration + 1}/{n_iter} - Losses: {losses}")

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    nlp.to_disk(output_path)
    print(f"Model saved to {output_path}")

# Train the model
train_ner(nlp, training_data, output_dir="model_output_blank", n_iter=20)
