"""Embedding Generation Service"""

import asyncio
import logging
import openai
from typing import List, Optional
import numpy as np
from functools import lru_cache

from esm.config import get_settings
from esm.utils.text_processing import chunk_text, clean_and_process_text

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing text embeddings"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        if self.settings.openai_api_key:
            openai.api_key = self.settings.openai_api_key
            self.client = openai
            logger.info("OpenAI client initialized")
        else:
            logger.warning("OpenAI API key not provided, embeddings will be disabled")
    
    async def generate_embedding(self, text: str, model: str = "text-embedding-ada-002") -> Optional[List[float]]:
        """Generate embedding for text"""
        if not self.client:
            logger.warning("OpenAI client not available, cannot generate embedding")
            return None
        
        try:
            # Clean and process text
            processed_text = clean_and_process_text(text)
            
            # Check text length (OpenAI has token limits)
            if len(processed_text) > 8000:  # Conservative limit
                processed_text = processed_text[:8000]
                logger.warning(f"Text truncated for embedding generation")
            
            # Generate embedding
            response = await asyncio.to_thread(
                self.client.embeddings.create,
                input=processed_text,
                model=model
            )
            
            if response and response.data:
                embedding = response.data[0].embedding
                logger.debug(f"Generated embedding with {len(embedding)} dimensions")
                return embedding
            
            logger.error("No embedding data in OpenAI response")
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    async def generate_batch_embeddings(
        self, 
        texts: List[str], 
        model: str = "text-embedding-ada-002",
        batch_size: int = 100
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts"""
        if not self.client:
            logger.warning("OpenAI client not available, cannot generate embeddings")
            return [None] * len(texts)
        
        try:
            results = []
            
            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Clean and process batch
                processed_batch = [
                    clean_and_process_text(text)[:8000]  # Truncate if needed
                    for text in batch
                ]
                
                try:
                    # Generate embeddings for batch
                    response = await asyncio.to_thread(
                        self.client.embeddings.create,
                        input=processed_batch,
                        model=model
                    )
                    
                    if response and response.data:
                        batch_embeddings = [item.embedding for item in response.data]
                        results.extend(batch_embeddings)
                        logger.debug(f"Generated {len(batch_embeddings)} embeddings in batch")
                    else:
                        logger.error(f"No embedding data in batch response")
                        results.extend([None] * len(batch))
                    
                    # Small delay between batches to respect rate limits
                    if i + batch_size < len(texts):
                        await asyncio.sleep(0.1)
                        
                except Exception as e:
                    logger.error(f"Failed to generate batch embeddings: {e}")
                    results.extend([None] * len(batch))
            
            return results
            
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            return [None] * len(texts)
    
    async def generate_chunked_embeddings(
        self, 
        text: str, 
        chunk_size: int = 1000,
        overlap: int = 100,
        model: str = "text-embedding-ada-002"
    ) -> List[tuple]:
        """Generate embeddings for text chunks with metadata"""
        try:
            # Split text into chunks
            chunks = chunk_text(text, chunk_size, overlap)
            
            if not chunks:
                return []
            
            # Generate embeddings for each chunk
            embeddings = await self.generate_batch_embeddings(chunks, model)
            
            # Combine chunks with embeddings and metadata
            results = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                if embedding:
                    results.append({
                        'chunk_index': i,
                        'chunk_text': chunk,
                        'embedding': embedding,
                        'chunk_size': len(chunk),
                        'start_pos': i * (chunk_size - overlap) if i > 0 else 0
                    })
                else:
                    logger.warning(f"Failed to generate embedding for chunk {i}")
            
            logger.info(f"Generated embeddings for {len(results)} chunks")
            return results
            
        except Exception as e:
            logger.error(f"Chunked embedding generation failed: {e}")
            return []
    
    @lru_cache(maxsize=1000)
    def calculate_similarity(self, embedding1: tuple, embedding2: tuple) -> float:
        """Calculate cosine similarity between embeddings (cached)"""
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    async def find_similar_embeddings(
        self, 
        query_embedding: List[float], 
        candidate_embeddings: List[tuple], 
        threshold: float = 0.7,
        top_k: int = 10
    ) -> List[tuple]:
        """Find most similar embeddings to query"""
        try:
            query_tuple = tuple(query_embedding)
            similarities = []
            
            for i, (candidate_id, candidate_embedding) in enumerate(candidate_embeddings):
                similarity = self.calculate_similarity(query_tuple, tuple(candidate_embedding))
                
                if similarity >= threshold:
                    similarities.append((candidate_id, similarity, i))
            
            # Sort by similarity (descending) and take top k
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to find similar embeddings: {e}")
            return []
    
    def get_embedding_stats(self, embeddings: List[List[float]]) -> dict:
        """Get statistics about embeddings"""
        try:
            if not embeddings:
                return {"count": 0}
            
            # Convert to numpy array for calculations
            embedding_array = np.array(embeddings)
            
            stats = {
                "count": len(embeddings),
                "dimensions": len(embeddings[0]) if embeddings else 0,
                "mean_magnitude": float(np.mean(np.linalg.norm(embedding_array, axis=1))),
                "std_magnitude": float(np.std(np.linalg.norm(embedding_array, axis=1))),
                "mean_values": embedding_array.mean(axis=0).tolist()[:10],  # First 10 dimensions
                "std_values": embedding_array.std(axis=0).tolist()[:10]     # First 10 dimensions
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to calculate embedding stats: {e}")
            return {"count": 0, "error": str(e)}
    
    async def health_check(self) -> dict:
        """Check embedding service health"""
        try:
            if not self.client:
                return {
                    "status": "unhealthy",
                    "error": "OpenAI client not initialized",
                    "api_key_configured": bool(self.settings.openai_api_key)
                }
            
            # Test with a simple embedding
            test_embedding = await self.generate_embedding("test")
            
            if test_embedding:
                return {
                    "status": "healthy",
                    "model": "text-embedding-ada-002",
                    "dimensions": len(test_embedding),
                    "api_key_configured": True
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": "Failed to generate test embedding",
                    "api_key_configured": bool(self.settings.openai_api_key)
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_key_configured": bool(self.settings.openai_api_key)
            }