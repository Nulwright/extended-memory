```python
"""Vector Operations Utilities"""

import numpy as np
from typing import List, Tuple, Optional
import logging
import math

logger = logging.getLogger(__name__)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    try:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        # Convert to numpy arrays for efficiency
        a = np.array(vec1)
        b = np.array(vec2)
        
        # Calculate dot product
        dot_product = np.dot(a, b)
        
        # Calculate magnitudes
        magnitude_a = np.linalg.norm(a)
        magnitude_b = np.linalg.norm(b)
        
        # Avoid division by zero
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = dot_product / (magnitude_a * magnitude_b)
        
        # Clamp to [-1, 1] range due to floating point precision
        return max(-1.0, min(1.0, float(similarity)))
        
    except Exception as e:
        logger.error(f"Cosine similarity calculation failed: {e}")
        return 0.0


def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
    """Calculate Euclidean distance between two vectors"""
    try:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return float('inf')
        
        # Convert to numpy arrays
        a = np.array(vec1)
        b = np.array(vec2)
        
        # Calculate Euclidean distance
        distance = np.linalg.norm(a - b)
        
        return float(distance)
        
    except Exception as e:
        logger.error(f"Euclidean distance calculation failed: {e}")
        return float('inf')


def manhattan_distance(vec1: List[float], vec2: List[float]) -> float:
    """Calculate Manhattan distance between two vectors"""
    try:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return float('inf')
        
        distance = sum(abs(a - b) for a, b in zip(vec1, vec2))
        return float(distance)
        
    except Exception as e:
        logger.error(f"Manhattan distance calculation failed: {e}")
        return float('inf')


def normalize_vector(vector: List[float]) -> List[float]:
    """Normalize vector to unit length"""
    try:
        if not vector:
            return []
        
        # Convert to numpy array
        vec = np.array(vector)
        
        # Calculate magnitude
        magnitude = np.linalg.norm(vec)
        
        # Avoid division by zero
        if magnitude == 0:
            return vector
        
        # Normalize
        normalized = vec / magnitude
        
        return normalized.tolist()
        
    except Exception as e:
        logger.error(f"Vector normalization failed: {e}")
        return vector


def vector_magnitude(vector: List[float]) -> float:
    """Calculate magnitude of a vector"""
    try:
        if not vector:
            return 0.0
        
        magnitude = math.sqrt(sum(x * x for x in vector))
        return magnitude
        
    except Exception as e:
        logger.error(f"Vector magnitude calculation failed: {e}")
        return 0.0


def dot_product(vec1: List[float], vec2: List[float]) -> float:
    """Calculate dot product of two vectors"""
    try:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        return sum(a * b for a, b in zip(vec1, vec2))
        
    except Exception as e:
        logger.error(f"Dot product calculation failed: {e}")
        return 0.0


def vector_add(vec1: List[float], vec2: List[float]) -> List[float]:
    """Add two vectors element-wise"""
    try:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return []
        
        return [a + b for a, b in zip(vec1, vec2)]
        
    except Exception as e:
        logger.error(f"Vector addition failed: {e}")
        return []


def vector_subtract(vec1: List[float], vec2: List[float]) -> List[float]:
    """Subtract two vectors element-wise"""
    try:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return []
        
        return [a - b for a, b in zip(vec1, vec2)]
        
    except Exception as e:
        logger.error(f"Vector subtraction failed: {e}")
        return []


def vector_scale(vector: List[float], scalar: float) -> List[float]:
    """Scale vector by a scalar value"""
    try:
        if not vector:
            return []
        
        return [x * scalar for x in vector]
        
    except Exception as e:
        logger.error(f"Vector scaling failed: {e}")
        return vector


def find_closest_vectors(
    query_vector: List[float], 
    candidate_vectors: List[Tuple[str, List[float]]], 
    top_k: int = 10,
    similarity_threshold: float = 0.0
) -> List[Tuple[str, float]]:
    """Find closest vectors to query vector using cosine similarity"""
    try:
        if not query_vector or not candidate_vectors:
            return []
        
        similarities = []
        
        for identifier, candidate_vector in candidate_vectors:
            similarity = cosine_similarity(query_vector, candidate_vector)
            
            if similarity >= similarity_threshold:
                similarities.append((identifier, similarity))
        
        # Sort by similarity (descending) and take top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
        
    except Exception as e:
        logger.error(f"Finding closest vectors failed: {e}")
        return []


def vector_centroid(vectors: List[List[float]]) -> Optional[List[float]]:
    """Calculate centroid (average) of multiple vectors"""
    try:
        if not vectors:
            return None
        
        # Check that all vectors have the same dimension
        dimensions = len(vectors[0])
        for vec in vectors:
            if len(vec) != dimensions:
                logger.error("Vectors must have same dimensions for centroid calculation")
                return None
        
        # Calculate average for each dimension
        centroid = []
        for i in range(dimensions):
            avg = sum(vec[i] for vec in vectors) / len(vectors)
            centroid.append(avg)
        
        return centroid
        
    except Exception as e:
        logger.error(f"Vector centroid calculation failed: {e}")
        return None


def calculate_vector_stats(vectors: List[List[float]]) -> dict:
    """Calculate statistics about a collection of vectors"""
    try:
        if not vectors:
            return {"count": 0}
        
        # Convert to numpy array for efficient calculations
        vector_array = np.array(vectors)
        
        stats = {
            "count": len(vectors),
            "dimensions": len(vectors[0]) if vectors else 0,
            "mean_magnitude": float(np.mean(np.linalg.norm(vector_array, axis=1))),
            "std_magnitude": float(np.std(np.linalg.norm(vector_array, axis=1))),
            "min_magnitude": float(np.min(np.linalg.norm(vector_array, axis=1))),
            "max_magnitude": float(np.max(np.linalg.norm(vector_array, axis=1))),
            "mean_values": np.mean(vector_array, axis=0).tolist(),
            "std_values": np.std(vector_array, axis=0).tolist()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Vector statistics calculation failed: {e}")
        return {"count": 0, "error": str(e)}


def is_valid_vector(vector: List[float], expected_dimension: Optional[int] = None) -> bool:
    """Validate that a vector is well-formed"""
    try:
        if not isinstance(vector, list):
            return False
        
        if len(vector) == 0:
            return False
        
        if expected_dimension is not None and len(vector) != expected_dimension:
            return False
        
        # Check that all elements are finite numbers
        for value in vector:
            if not isinstance(value, (int, float)):
                return False
            if not math.isfinite(value):
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Vector validation failed: {e}")
        return False
