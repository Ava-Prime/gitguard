#!/usr/bin/env python3
"""
Embeddings module for semantic search functionality.

This module provides text embedding capabilities for GitGuard's knowledge graph,
enabling semantic search over PR summaries, titles, and other textual content.
"""

import logging
from typing import List, Optional
import os

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

logger = logging.getLogger(__name__)

def embed(text: str) -> List[float]:
    """
    Generate embeddings for the given text using the model router.
    
    This function hooks into your model router to generate 1536-dimensional
    embeddings for semantic search. If the embedding service is unavailable
    or fails, returns an empty list to gracefully skip embedding storage.
    
    Args:
        text: The text to embed (PR summary, title, etc.)
        
    Returns:
        List of 1536 floats representing the text embedding,
        or empty list if embedding fails or is unavailable
    """
    if not text or not text.strip():
        return []
    
    if not REQUESTS_AVAILABLE:
        logger.warning("Requests module not available, embedding generation disabled")
        return []
    
    try:
        # Hook to your model router here
        # This is a placeholder implementation that you should replace
        # with your actual model router endpoint
        
        router_url = os.getenv('MODEL_ROUTER_URL')
        if not router_url:
            logger.debug("MODEL_ROUTER_URL not configured, skipping embeddings")
            return []
        
        # Example API call to model router
        # Replace this with your actual router interface
        response = requests.post(
            f"{router_url}/embed",
            json={
                "text": text,
                "model": "text-embedding-3-large",  # or your preferred model
                "dimensions": 1536
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            embedding = data.get('embedding', [])
            
            # Validate embedding dimensions
            if len(embedding) == 1536:
                return embedding
            else:
                logger.warning(f"Unexpected embedding dimension: {len(embedding)}, expected 1536")
                return []
        else:
            logger.warning(f"Embedding API returned status {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Embedding request failed: {e}")
        return []

def embed_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batch.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embeddings, same order as input texts.
        Failed embeddings are returned as empty lists.
    """
    if not texts:
        return []
    
    if not REQUESTS_AVAILABLE:
        logger.warning("Requests module not available, batch embedding generation disabled")
        return [[] for _ in texts]
    
    try:
        router_url = os.getenv('MODEL_ROUTER_URL')
        if not router_url:
            logger.debug("MODEL_ROUTER_URL not configured, skipping batch embeddings")
            return [[] for _ in texts]
        
        # Batch API call to model router
        response = requests.post(
            f"{router_url}/embed/batch",
            json={
                "texts": texts,
                "model": "text-embedding-3-large",
                "dimensions": 1536
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            embeddings = data.get('embeddings', [])
            
            # Validate and return embeddings
            result = []
            for i, embedding in enumerate(embeddings):
                if len(embedding) == 1536:
                    result.append(embedding)
                else:
                    logger.warning(f"Invalid embedding dimension for text {i}: {len(embedding)}")
                    result.append([])
            
            return result
        else:
            logger.warning(f"Batch embedding API returned status {response.status_code}")
            return [[] for _ in texts]
            
    except Exception as e:
        logger.error(f"Batch embedding failed: {e}")
        return [[] for _ in texts]

def store_embedding(node_id: str, embedding: List[float], model: str = "text-embedding-3-large") -> bool:
    """
    Store embedding in the database.
    
    Args:
        node_id: UUID of the node to associate with the embedding
        embedding: The 1536-dimensional embedding vector
        model: Name of the embedding model used
        
    Returns:
        True if stored successfully, False otherwise
    """
    if not embedding or len(embedding) != 1536:
        return False
    
    try:
        from .activities import _conn
        
        with _conn() as c, c.cursor() as cur:
            cur.execute(
                """
                INSERT INTO codex_embeddings (node_id, model, vector) 
                VALUES (%s, %s, %s)
                ON CONFLICT (node_id) DO UPDATE SET
                    model = EXCLUDED.model,
                    vector = EXCLUDED.vector
                """,
                (node_id, model, embedding)
            )
            return True
            
    except Exception as e:
        logger.error(f"Failed to store embedding for node {node_id}: {e}")
        return False

def search_similar(query_text: str, limit: int = 20) -> List[dict]:
    """
    Search for similar content using semantic similarity.
    
    Args:
        query_text: The search query text
        limit: Maximum number of results to return
        
    Returns:
        List of dictionaries containing node information and similarity scores
    """
    query_embedding = embed(query_text)
    if not query_embedding:
        logger.warning("Could not generate embedding for query, falling back to empty results")
        return []
    
    try:
        from .activities import _conn
        
        with _conn() as c, c.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    n.ntype, 
                    n.nkey, 
                    n.title, 
                    n.data,
                    1 - (e.vector <=> %s) AS score
                FROM codex_nodes n
                JOIN codex_embeddings e ON e.node_id = n.id
                ORDER BY e.vector <=> %s
                LIMIT %s
                """,
                (query_embedding, query_embedding, limit)
            )
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'type': row['ntype'],
                    'key': row['nkey'],
                    'title': row['title'],
                    'data': row['data'],
                    'score': float(row['score'])
                })
            
            return results
            
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return []