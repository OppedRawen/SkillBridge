import spacy

# Load the pipeline
nlp = spacy.load("model_output/model-best")

# Some test text
text = "We're looking for a developer with experience in iOS development and Docker."

# Process the text
doc = nlp(text)

# Print recognized entities
for ent in doc.ents:
    print(ent.text, ent.label_)
