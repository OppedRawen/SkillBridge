from pdfminer.high_level import extract_text
import tempfile
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_file_or_path):
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_file_or_path: UploadFile from FastAPI, file-like object, or a dictionary containing a file
        
    Returns:
        str: Extracted text content
    """
    temp_path = None
    
    try:
        logger.info("Extracting text from PDF file object")
        
        # Handle different input types
        if isinstance(pdf_file_or_path, dict) and 'file' in pdf_file_or_path:
            # If it's a dictionary with a 'file' key, extract the file object
            file_obj = pdf_file_or_path['file']
        else:
            # Otherwise assume it's already a file object or UploadFile
            file_obj = pdf_file_or_path
            
        # Check if it's a file-like object with a read method
        if hasattr(file_obj, 'read'):
            # Save content to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                content = file_obj.read()
                temp_file.write(content)
                temp_path = temp_file.name
                
        # Check if it's a path string
        elif isinstance(pdf_file_or_path, str) and os.path.exists(pdf_file_or_path):
            temp_path = pdf_file_or_path
        else:
            raise ValueError(f"Unsupported input type: {type(pdf_file_or_path)}")
        
        # Extract text from the PDF
        text = extract_text(temp_path)
        
        # Check if extraction was successful
        if not text or len(text.strip()) == 0:
            logger.warning(f"Extracted empty text from PDF")
            text = "No text could be extracted from this PDF. Please try a different file."
        else:
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
        
        # Clean up the temporary file if we created one
        if temp_path and pdf_file_or_path != temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
            logger.debug(f"Deleted temporary file: {temp_path}")
        
        return text
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        
        # Clean up the temporary file if it exists
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass
                
        # Return error message instead of raising exception
        return f"Error extracting text from PDF: {str(e)}"