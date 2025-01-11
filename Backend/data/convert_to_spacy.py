import srsly
import spacy
from spacy.tokens import DocBin

def convert_json_to_spacy(input_json_path, output_spacy_path):
    """
    Reads a JSON file of the form:
    [
      {
        "text": "...",
        "ents": [
          {"start": ..., "end": ..., "label": "SKILL"},
          ...
        ]
      },
      ...
    ]
    Then writes a spaCy DocBin file to output_spacy_path for training.
    """
    nlp = spacy.blank("en")  # create a blank English pipeline
    db = DocBin()

    data = srsly.read_json(input_json_path)

    for record in data:
        text = record["text"]
        ents_info = record["ents"]

        doc = nlp.make_doc(text)
        spans = []
        for ent in ents_info:
            start = ent["start"]
            end = ent["end"]
            label = ent["label"]
            # Create a span if valid
            span = doc.char_span(start, end, label=label)
            if span is not None:
                spans.append(span)

        valid_spans = []
        for span in spans:
            # If it doesn’t overlap with any already-chosen span, add it
            if not any(s.start < span.end and span.start < s.end for s in valid_spans):
                valid_spans.append(span)

        doc.ents = valid_spans
        db.add(doc)

    db.to_disk(output_spacy_path)
    print(f"Converted {input_json_path} -> {output_spacy_path}")

if __name__ == "__main__":
    # Example usage:
    convert_json_to_spacy("train.json", "train.spacy")
    convert_json_to_spacy("dev.json", "dev.spacy")
