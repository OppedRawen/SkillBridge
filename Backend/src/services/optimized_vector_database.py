import os
import logging
import numpy as np
import chromadb
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class OptimizedVectorDatabase:
    """An optimized version of the vector database using in-memory ChromaDB."""
    
    def __init__(self):
        """
        Initialize the vector database using in-memory ChromaDB.
        """
        try:
            self.skills_collection = self.client.get_collection(name="skills")
            logger.info("Using existing 'skills' collection")
        except Exception:
            # Collection doesn't exist, create it
            self.skills_collection = self.client.create_collection(
                name="skills",
                metadata={"description": "Skill embeddings for job matching"},
                embedding_function=None
            )
            logger.info("Created new 'skills' collection")
        
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
            # Process in smaller batches to avoid memory issues
            batch_size = 10
            for i in range(0, len(skill_ids), batch_size):
                batch_ids = skill_ids[i:i+batch_size]
                batch_texts = skill_texts[i:i+batch_size]
                batch_embeddings = embeddings[i:i+batch_size]
                batch_metadatas = metadatas[i:i+batch_size]
                
                # Convert numpy arrays to lists
                batch_embedding_lists = [emb.tolist() for emb in batch_embeddings]
                
                # Add the batch
                self.skills_collection.upsert(
                    ids=batch_ids,
                    embeddings=batch_embedding_lists,
                    documents=batch_texts,
                    metadatas=batch_metadatas
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
            
            # Search the collection - explicitly use L2 similarity
            results = self.skills_collection.query(
                query_embeddings=[query_list],
                n_results=min(limit, 20)  # Limit to avoid memory issues
            )
            
            # Process results
            matches = []
            if results and 'ids' in results and len(results['ids']) > 0:
                ids = results['ids'][0]
                documents = results['documents'][0] if 'documents' in results and len(results['documents']) > 0 else []
                distances = results['distances'][0] if 'distances' in results and len(results['distances']) > 0 else []
                metadatas = results['metadatas'][0] if 'metadatas' in results and len(results['metadatas']) > 0 else []
                
                for i in range(len(ids)):
                    if i < len(documents) and i < len(distances):
                        skill_id = ids[i]
                        skill_text = documents[i]
                        distance = distances[i]
                        
                        # Convert distance to similarity (ChromaDB returns L2 distance)
                        similarity = 1.0 / (1.0 + distance)
                        
                        # Only include if above threshold
                        if similarity >= threshold:
                            metadata = metadatas[i] if i < len(metadatas) else {}
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
            
            if result and 'documents' in result and len(result['documents']) > 0:
                document = result['documents'][0]
                embedding = np.array(result['embeddings'][0]) if 'embeddings' in result and len(result['embeddings']) > 0 else None
                metadata = result['metadatas'][0] if 'metadatas' in result and len(result['metadatas']) > 0 else {}
                
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