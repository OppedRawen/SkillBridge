from transformers import pipeline
def load_bart_summarizer(model_name: str="facebook/bart-large-cnn"):
    summarizer = pipeline("summarization",model=model_name)
    return summarizer
def generate_summary_or_recommendation(text:str,summarizer_pipeline,max_len = 100,min_len = 30)->str:
    result = summarizer_pipeline(
        text,
        max_len=max_len,
        min_len=min_len,
        do_sample = False #deterministic output

    )

    return result[0]["summary_text"]

