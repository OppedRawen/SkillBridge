import json


def generate_report(analysis:dict,output_file:str = None):
    """
    Generate a skill gap report based on the analysis and optionally save it to a file.

    Args:
        analysis (dict): The skill gap analysis result (matched and missing skills).
        output_file (str, optional): Path to save the report as a JSON file. Defaults to None.

    Returns:
        str: A formatted string of the report for console output.
    """
    matched = ", ".join(sorted(analysis["matched_skills"]))
    missing = ", ".join(sorted(analysis["missing_skills"]))

    report = (
        f"Skill Gap Analysis Report:\n"
        f"==========================\n"
        f"Matched Skills:\n  {matched if matched else 'None'}\n\n"
        f"Missing Skills:\n  {missing if missing else 'None'}\n"
    )

    if output_file:
        with open(output_file, 'w') as f:
            json.dump(analysis,f, indent=4)
        report+= f"\nReport saved to: {output_file}\n"
    return report