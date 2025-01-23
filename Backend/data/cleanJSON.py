import json

def fix_json_file(input_file, output_file):
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Clean and combine all lines
        cleaned_json = "[\n" + ",\n".join(line.strip() for line in lines if line.strip()) + "\n]"

        # Validate the JSON structure
        json.loads(cleaned_json)  # Will raise an error if the JSON is invalid

        # Save the cleaned JSON
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(cleaned_json)

        print(f"✅ JSON file successfully cleaned and saved to {output_file}")

    except json.JSONDecodeError as e:
        print(f"❌ JSON Decode Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

# Input and output file paths
input_file = "EntityRecognitioninResumes.json"
output_file = "Cleaned_Entity_Recognition.json"

fix_json_file(input_file, output_file)
