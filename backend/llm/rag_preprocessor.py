"""
RAG Content Preprocessor Module

This module provides functionality to preprocess RAG (Retrieval-Augmented Generation) 
content before feeding it to the main LLM generation pipeline. The preprocessor 
combines compression and simplification:

- Summarizes content to 50 words or less for efficiency
- Converts academic language to simple, easy-to-understand text
- Makes research findings accessible for story generation

This improves generation quality, speed, and makes academic research accessible
for story generation about memory technology futures.
"""

import requests
import logging
from typing import Optional

# Handle imports for both relative (Django) and absolute (standalone) usage
try:
    from ..shared.constants import OLLAMA_PREPROCESS_MODEL
except ImportError:
    from shared.constants import OLLAMA_PREPROCESS_MODEL

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_PREPROCESS_MODEL = OLLAMA_PREPROCESS_MODEL

logger = logging.getLogger(__name__)


def create_preprocessing_prompt(content: str) -> str:
    """
    Create preprocessing prompt for RAG content summarization and simplification
    
    Args:
        content: The content to be preprocessed
        
    Returns:
        str: The preprocessing prompt
    """
    return f"""
You are a science communicator who transforms complex academic research into simple, easy-to-understand content about memory technology and ethics.

Your task: Convert the following academic research into simple, plain language that anyone can understand while preserving the most important facts.

CRITICAL REQUIREMENTS:
- STRICT WORD LIMIT: Output must be EXACTLY 50 words or fewer
- COUNT YOUR WORDS: Ensure final output does not exceed 50 words
- MANDATORY: If your summary approaches 50 words, stop immediately

SIMPLIFICATION RULES:
- Replace jargon with everyday words
- Explain technical terms in simple language
- Use short, clear sentences
- Avoid academic phrases and complex terminology
- Focus on what this means for regular people
- Preserve key facts, numbers, and implications

CONTENT FOCUS:
- Research findings about memory technology
- What this technology can do
- Ethical concerns and risks
- Impact on society

RESEARCH CONTENT:
{content}

OUTPUT FORMAT:
Return simple, clear explanations that a 12-year-old could understand, while keeping essential information for story generation.

FINAL CHECK: Before submitting, count your words. Your response must be 50 words or fewer and use simple language.
""".strip()


def call_preprocess_model(prompt: str, timeout: int = 45) -> Optional[str]:
    """
    Call the preprocessing model via Ollama API
    
    Args:
        prompt: The preprocessing prompt
        timeout: Timeout duration in seconds
        
    Returns:
        Optional[str]: Preprocessing result as plain text, None if failed
    """
    try:
        payload = {
            "model": DEFAULT_PREPROCESS_MODEL,
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        
        data = response.json()
        result = data.get("response", "").strip()
        
        # Validate result quality - check word count, not character count
        word_count = len(result.split())
        if word_count >= 10:  # Ensure substantial content (minimum 10 words)
            return result
        else:
            logger.warning(f"Preprocessor returned short result: {word_count} words")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("Preprocessing timeout - Ollama API took too long to respond")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Preprocessing network error: {e}")
        return None
    except Exception as e:
        logger.error(f"Preprocessing unexpected error: {e}")
        return None


def preprocess_rag_content(content: str) -> str:
    """
    Preprocess RAG content by extracting key information and making it accessible
    Compresses content to 50 words while making academic language easy to understand
    
    Args:
        content: The RAG content string to be preprocessed
        
    Returns:
        str: The preprocessed content (compressed + simplified)
    """
    # Check input
    if not content or not content.strip():
        logger.debug("Empty content, returning as-is")
        return content
    
    # Check word count, only preprocess if greater than 50 words
    word_count = len(content.split())
    if word_count <= 50:
        logger.debug(f"Content already short ({word_count} words), skipping preprocessing")
        return content
    
    logger.info(f"Starting preprocessing: {word_count} words → target 50 words + simplification")
    
    # Create preprocessing prompt (includes both compression and simplification)
    prompt = create_preprocessing_prompt(content)
    
    # Call preprocessing model
    processed_content = call_preprocess_model(prompt)
    
    if processed_content:
        processed_words = len(processed_content.split())
        logger.info(f"Preprocessing successful: {word_count} → {processed_words} words (compressed & simplified)")
        return processed_content
    else:
        # Preprocessing failed, return original content
        logger.warning("Preprocessing failed, returning original content")
        return content


def preprocess_rag_chunks(rag_chunks: list[dict]) -> str:
    """
    Preprocess RAG chunks and format them for LLM input
    First format and combine all chunks, then compress and simplify the entire content
    
    Args:
        rag_chunks: List of RAG retrieved chunks
        
    Returns:
        str: Formatted and preprocessed context string (compressed + simplified)
    """
    if not rag_chunks:
        return ""
    
    # Step 1: Format all chunks following original format_rag_context_for_llm logic
    formatted_chunks = []
    for i, chunk in enumerate(rag_chunks, 1):
        meta = chunk.get("meta", {})
        title = meta.get("title") or meta.get("article_title", "Unknown Source")
        text = chunk.get("text", "")
        formatted_chunks.append(f"[{i}] {title}: {text}")
    
    # Step 2: Combine all chunks into a single string
    combined_content = "\n\n".join(formatted_chunks)
    
    # Step 3: Preprocess the entire content (compress to 50 words + simplify language)
    processed_content = preprocess_rag_content(combined_content)
    return processed_content

