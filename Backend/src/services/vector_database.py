import os
import logging
import pickle
import numpy as np
from pathlib import Path
import chromadb
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class VectorDatabase:
    """A simple vector database for storing and retrieving skill embeddings."""
    
    def __init__(self, persist_directory="./vector_db"):
        """
        Initialize the vector database.
        
        Args:
            persist_directory (str): Directory to persist the database
        """
        try:
            # Create the directory if it doesn't exist
            Path(persist_directory).mkdir(parents=True, exist_ok=True)
            
            # Initialize Chroma client (in-memory for simplicity, but could be persistent)
            self.client = chromadb.Client()
            
            # Create or get the skills collection
            self.skills_collection = self.client.create_collection(
                name="skills",
                metadata={"description": "Skill embeddings for job matching"}
            )
            
            logger.info(f"Vector database initialized with collection 'skills'")
        except Exception as e:
            logger.error(f"Error initializing vector database: {str(e)}")
            raise
    
    def add_or_update_skill(self, skill_id, skill_text, embedding, metadata=None):
        """
        Add or update a skill in the database.
        
        Args:
            skill_id (str): Unique identifier for the skill
            skill_text (str): The skill text
            embedding (numpy.ndarray): Vector embedding of the skill
            metadata (dict): Additional metadata about the skill
        
        Returns:
            bool: Success status
        """
        if metadata is None:
            metadata = {}
            
        try:
            # Convert numpy array to list for storage
            embedding_list = embedding.tolist()
            
            # Add or update the embedding
            self.skills_collection.upsert(
                ids=[skill_id],
                embeddings=[embedding_list],
                documents=[skill_text],
                metadatas=[metadata]
            )
            
            logger.debug(f"Skill '{skill_text}' added/updated with ID: {skill_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding/updating skill: {str(e)}")
            return False
    
    def add_skills_batch(self, skill_ids, skill_texts, embeddings, metadatas=None):
        """
        Add multiple skills to the database in a batch.
        
        Args:
            skill_ids (list): List of unique identifiers
            skill_texts (list): List of skill texts
            embeddings (list): List of embeddings
            metadatas (list): List of metadata dictionaries
            
        Returns:
            bool: Success status
        """
        if not skill_ids or not skill_texts or not embeddings:
            logger.warning("Empty input for batch addition")
            return False
            
        if len(skill_ids) != len(skill_texts) or len(skill_ids) != len(embeddings):
            logger.error("Mismatched lengths for batch addition")
            return False
            
        if metadatas is None:
            metadatas = [{} for _ in skill_ids]
            
        try:
            # Convert numpy arrays to lists
            embedding_lists = [emb.tolist() for emb in embeddings]
            
            # Add the batch
            self.skills_collection.upsert(
                ids=skill_ids,
                embeddings=embedding_lists,
                documents=skill_texts,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(skill_ids)} skills to the database")
            return True
        except Exception as e:
            logger.error(f"Error adding skills batch: {str(e)}")
            return False
    
    def search_similar_skills(self, query_embedding, limit=5, threshold=0.6):
        """
        Search for skills similar to the query embedding.
        
        Args:
            query_embedding (numpy.ndarray): Query embedding
            limit (int): Maximum number of results
            threshold (float): Similarity threshold
            
        Returns:
            list: List of (skill_id, skill_text, score, metadata) tuples
        """
        try:
            # Convert to list for query
            query_list = query_embedding.tolist()
            
            # Search the collection
            results = self.skills_collection.query(
                query_embeddings=[query_list],
                n_results=limit
            )
            
            # Process results
            matches = []
            if results and results['ids'] and results['documents'] and results['distances']:
                for i, (skill_id, skill_text, distance) in enumerate(zip(
                    results['ids'][0], 
                    results['documents'][0], 
                    results['distances'][0]
                )):
                    # Convert distance to similarity (ChromaDB returns L2 distance)
                    similarity = 1.0 / (1.0 + distance)
                    
                    # Only include if above threshold
                    if similarity >= threshold:
                        metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                        matches.append((skill_id, skill_text, similarity, metadata))
            
            return matches
        except Exception as e:
            logger.error(f"Error searching similar skills: {str(e)}")
            return []
    
    def get_skill(self, skill_id):
        """
        Retrieve a skill by its ID.
        
        Args:
            skill_id (str): Unique identifier for the skill
            
        Returns:
            tuple: (skill_text, embedding, metadata) or None if not found
        """
        try:
            result = self.skills_collection.get(ids=[skill_id])
            
            if result and result['documents'] and len(result['documents']) > 0:
                document = result['documents'][0]
                embedding = np.array(result['embeddings'][0]) if result['embeddings'] else None
                metadata = result['metadatas'][0] if result['metadatas'] else {}
                
                return (document, embedding, metadata)
            
            return None
        except Exception as e:
            logger.error(f"Error getting skill: {str(e)}")
            return None
    
    def delete_skill(self, skill_id):
        """
        Delete a skill from the database.
        
        Args:
            skill_id (str): Unique identifier for the skill
            
        Returns:
            bool: Success status
        """
        try:
            self.skills_collection.delete(ids=[skill_id])
            logger.debug(f"Skill with ID {skill_id} deleted")
            return True
        except Exception as e:
            logger.error(f"Error deleting skill: {str(e)}")
            return False