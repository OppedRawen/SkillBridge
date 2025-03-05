import os
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# # Path to the local Llama 2 folder
# current_dir = os.path.dirname(__file__)
# LLAMA2_PATH = os.path.join(os.path.dirname(__file__), "..\..", "Llama-2-7b-chat-hf")

model_path = "meta-llama/Llama-2-7b-chat-hf"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
        model_path,
        device_map="auto",   # or "cpu"
        torch_dtype="float16" # if GPU
    )
# Global variables to hold model + pipeline
llm_pipeline = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_length=512,
        temperature=0.7,
        top_p=0.9
    )

# def get_llama_pipeline():
#     global _llama_pipeline
#     if _llama_pipeline is None:
#         print("Loading Llama 2 from:", LLAMA2_PATH)
#         tokenizer = AutoTokenizer.from_pretrained(LLAMA2_PATH)
#         model = AutoModelForCausalLM.from_pretrained(
#             LLAMA2_PATH,
#             device_map="auto",   # or {"": "cpu"} if no GPU
#             torch_dtype="float16"  # if GPU and 16-bit
#         )
#         _llama_pipeline = pipeline(
#             "text-generation",
#             model=model,
#             tokenizer=tokenizer,
#             max_length=512,
#             temperature=0.7,
#             top_p=0.9
#         )
#     return _llama_pipeline

def generate_recommendations(skill_list):
    """
    skill_list: e.g. [("React", 3.0), ("AWS", 2.5), ("Laravel", 2.5)]
    """
    # pipeline = get_llama_pipeline()
    
    # Build a prompt that instructs the model to provide recommendations
    top_skills_str = "\n".join([f"- {s[0]} (Weight: {s[1]})" for s in skill_list])
    prompt = f"""
You are a helpful AI assistant specialized in career development.
The user is missing the following top skills from a job description:
{top_skills_str}

Explain why each skill is important for this role, and suggest ways to learn it
(e.g. books, websites, or courses). Return your answer in a concise bullet-point list.
    """
    outputs = llm_pipeline(prompt, max_new_tokens=200, do_sample=True,truncation=True)
    
    # The pipeline returns a list of dicts with "generated_text"
    generated_text = outputs[0]["generated_text"]
    return generated_text
