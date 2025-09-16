"""
RAG Integration Adapter for LLM Generate Functions

This module provides adapter functions to bridge the gap between
LLM generation output and RAG retrieval input.
"""

import json
from typing import Dict, Any, List, Union
from rag.retrieve import retrieve_chunks


def get_rag_context(llm_result: Union[str, Dict[str, Any]]) -> str:
    """
    Extract query text from LLM result for RAG retrieval.
    
    Args:
        llm_result: Result from generate_question() or generate_description()
                   Can be either JSON string or dict (for backward compatibility)
        
    Returns:
        str: Query text for RAG retrieval
    """
    # Handle both JSON string and dict formats
    if isinstance(llm_result, str):
        try:
            parsed_result = json.loads(llm_result)
            return parsed_result.get("query_text", "")
        except json.JSONDecodeError:
            return ""
    elif isinstance(llm_result, dict):
        # Backward compatibility for dict format
        return llm_result.get("query_text", "")
    else:
        return ""


def format_rag_context_for_llm(rag_chunks: List[Dict]) -> str:
    """
    Format RAG chunks into a context string for LLM input.
    
    Args:
        rag_chunks: List of chunks from retrieve_chunks()
        
    Returns:
        str: Formatted context string for LLM
    """
    if not rag_chunks:
        return ""
    
    formatted_chunks = []
    for i, chunk in enumerate(rag_chunks, 1):
        meta = chunk.get("meta", {})
        title = meta.get("title") or meta.get("article_title", "Unknown Source") # Change after rag-2 merged
        text = chunk.get("text", "")
        formatted_chunks.append(f"[{i}] {title}: {text}")
    
    return "\n\n".join(formatted_chunks)
