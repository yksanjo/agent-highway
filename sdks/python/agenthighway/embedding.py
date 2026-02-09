"""
Simple embedding/vector operations

In production, use sentence-transformers or OpenAI embeddings.
This is a lightweight fallback.
"""

import hashlib
import numpy as np
from typing import List


def embed(text: str, dimensions: int = 64) -> List[float]:
    """
    Create a simple embedding vector from text.
    
    Uses hash-based approach for deterministic results.
    For production, replace with proper embeddings.
    
    Args:
        text: Input text
        dimensions: Vector dimensions (default 64)
        
    Returns:
        Normalized vector
    """
    # Create hash
    hash_obj = hashlib.sha256(text.encode())
    hash_bytes = hash_obj.digest()
    
    # Convert to vector
    vec = []
    for i in range(dimensions):
        # Use different parts of hash
        idx = i % len(hash_bytes)
        val = hash_bytes[idx] / 255.0  # Normalize to 0-1
        vec.append(val - 0.5)  # Center around 0
    
    # Normalize to unit vector
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = [v / norm for v in vec]
    
    return vec


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(a) != len(b):
        return 0.0
    
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot / (norm_a * norm_b)


def resonance_match(focus: List[float], signal_resonance: List[float]) -> float:
    """
    Calculate how well a signal resonates with an agent's focus.
    
    Returns value 0-1 where 1 is perfect match.
    """
    return cosine_similarity(focus, signal_resonance)
