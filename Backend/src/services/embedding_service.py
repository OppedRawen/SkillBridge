import os
import logging
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class EmbeddingService:
    """Service for generating and comparing text embeddings."""
    
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Initialize the embedding service with a specific model.
        
        Args:
            model_name (str): Name of the sentence-transformers model to use
        """
        try:
            logger.info(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            raise

    def get_embedding(self, text):
        """
        Generate embeddings for a single text string.
        
        Args:
            text (str): Text to embed
            
        Returns:
            numpy.ndarray: Embedding vector
        """
        if not text or not isinstance(text, str):
            logger.warning(f"Invalid text for embedding: {type(text)}")
            return None
            
        try:
            return self.model.encode(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def get_embeddings(self, texts):
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts (list): List of text strings
            
        Returns:
            numpy.ndarray: Array of embedding vectors
        """
        if not texts:
            logger.warning("Empty text list for embeddings")
            return np.array([])
            
        # Filter out None or empty strings
        valid_texts = [t for t in texts if t and isinstance(t, str)]
        
        if not valid_texts:
            logger.warning("No valid texts for embeddings")
            return np.array([])
            
        try:
            return self.model.encode(valid_texts)
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return np.array([])
    
    def calculate_similarity(self, embedding1, embedding2):
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1 (numpy.ndarray): First embedding
            embedding2 (numpy.ndarray): Second embedding
            
        Returns:
            float: Similarity score between 0 and 1
        """
        if embedding1 is None or embedding2 is None:
            return 0.0
            
        try:
            # Reshape for sklearn's cosine_similarity
            e1 = embedding1.reshape(1, -1)
            e2 = embedding2.reshape(1, -1)
            return cosine_similarity(e1, e2)[0][0]
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    def find_best_matches(self, query_embeddings, candidate_embeddings, candidates, threshold=0.6):
        """
        Find best matching candidates for each query based on embedding similarity.
        
        Args:
            query_embeddings (numpy.ndarray): Embeddings of queries
            candidate_embeddings (numpy.ndarray): Embeddings of candidates
            candidates (list): Original candidate texts
            threshold (float): Minimum similarity threshold
            
        Returns:
            dict: Dictionary mapping each query to its matches with similarity scores
        """
        if len(query_embeddings) == 0 or len(candidate_embeddings) == 0:
            return {}
            
        try:
            # Calculate similarity matrix
            similarity_matrix = cosine_similarity(query_embeddings, candidate_embeddings)
            
            matches = {}
            for i, similarities in enumerate(similarity_matrix):
                # Find indices of matches above threshold
                match_indices = np.where(similarities >= threshold)[0]
                
                # Create dictionary of matches with scores
                matches[i] = {
                    candidates[idx]: float(similarities[idx]) 
                    for idx in match_indices
                }
                
            return matches
        except Exception as e:
            logger.error(f"Error finding best matches: {str(e)}")
            return {}