from pdfminer.high_level import extract_text
import tempfile
import os
import logging
import platform
import time

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_file_or_path):
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_file_or_path: Either a file path string or an open file object
        
    Returns:
        str: Extracted text content
    """
    temp_path = None
    try:
        # Handle different input types
        if isinstance(pdf_file_or_path, str):
            # It's a file path
            logger.info(f"Extracting text from PDF path: {pdf_file_or_path}")
            text = extract_text(pdf_file_or_path)
            return text
        else:
            # Assume it's an open file object
            logger.info(f"Extracting text from PDF file object")
            
            # Create a unique temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                content = pdf_file_or_path.read()
                temp_file.write(content)
                temp_path = temp_file.name
            
            logger.info(f"Created temporary file: {temp_path}")
            
            # Windows compatibility: close file and wait a moment
            if platform.system() == 'Windows':
                time.sleep(0.1)  # Short delay to ensure file is released
            
            # Extract text from the temporary file
            text = extract_text(temp_path)
            
            return text
            
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise Exception(f"Error extracting text from PDF: {str(e)}")
    finally:
        # Clean up in the finally block to ensure it runs
        if temp_path and os.path.exists(temp_path):
            try:
                # Wait a moment on Windows before trying to delete
                if platform.system() == 'Windows':
                    time.sleep(0.1)
                    
                os.unlink(temp_path)
                logger.info(f"Deleted temporary file: {temp_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete temporary file: {str(cleanup_error)}")