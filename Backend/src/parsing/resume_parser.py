import PyPDF2
import os

def parse_resume_pdf(pdf_file_path:str)->str:

    if not os.path.exists(pdf_file_path):
        raise FileNotFoundError(f"File at path {pdf_file_path} not found")
    
    text_content=[]
    with open(pdf_file_path,'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)

        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text.strip())

    return '\n'.join(text_content)