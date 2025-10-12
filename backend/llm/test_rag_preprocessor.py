#!/usr/bin/env python3
"""
RAG Preprocessor Test

Tests the rag_preprocessor functionality to verify chunks are properly processed
and simplified for LLM input.
"""

import os
import sys
import logging
import django

# Configure logging to reduce noise
logging.getLogger('rag.setup').setLevel(logging.WARNING)
logging.getLogger('rag.retrieve').setLevel(logging.WARNING)
logging.getLogger('faiss.loader').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)

# Keep preprocessor logging
logging.getLogger('llm.rag_preprocessor').setLevel(logging.INFO)

# Set up Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'memory_sim.settings')
django.setup()

from rag.retrieve import retrieve_chunks
from llm.rag_preprocessor import preprocess_rag_chunks, preprocess_rag_content


def test_rag_retrieval():
    """Test basic RAG retrieval without preprocessing"""
    print("=== Testing Basic RAG Retrieval ===")
    print()
    
    query = "memory consolidation during sleep"
    print(f"Query: {query}")
    print()
    
    try:
        chunks = retrieve_chunks(query)
        print(f"Retrieved {len(chunks)} chunks:")
        print()
        
        for i, chunk in enumerate(chunks[:2], 1):  # Show first 2 chunks
            meta = chunk.get("meta", {})
            title = meta.get("title") or meta.get("article_title", "Unknown Source")
            text = chunk.get("text", "")
            
            print(f"Chunk {i}:")
            print(f"  Title: {title}")
            print(f"  Text length: {len(text)} characters, {len(text.split())} words")
            print(f"  First 200 chars: {text[:200]}...")
            print()
        
        return chunks
        
    except Exception as e:
        print(f"RAG retrieval failed: {e}")
        return []


def test_rag_preprocessing():
    """Test RAG preprocessing with chunks"""
    print("=== Testing RAG Preprocessing ===")
    print()
    
    query = "memory consolidation during sleep"
    print(f"Query: {query}")
    print()
    
    try:
        # Get raw chunks
        chunks = retrieve_chunks(query)
        print(f"Retrieved {len(chunks)} raw chunks")
        
        # Calculate original content size
        total_words = 0
        for chunk in chunks:
            text = chunk.get("text", "")
            total_words += len(text.split())
        
        print(f"Original total content: {total_words} words")
        print()
        
        # Process chunks
        processed_content = preprocess_rag_chunks(chunks)
        processed_words = len(processed_content.split()) if processed_content else 0
        
        print(f"Processed content: {processed_words} words")
        print()
        print("Processed content:")
        print("-" * 50)
        print(processed_content)
        print("-" * 50)
        print()
        
        # Verify compression
        if total_words > 50 and processed_words <= 50:
            print(f"SUCCESS: Content compressed from {total_words} to {processed_words} words")
        elif total_words <= 50:
            print(f"INFO: Original content was already short ({total_words} words)")
        else:
            print(f"WARNING: Content not properly compressed ({total_words} -> {processed_words} words)")
        
        return processed_content
        
    except Exception as e:
        print(f"RAG preprocessing failed: {e}")
        return ""


def test_direct_preprocessing():
    """Test preprocessing with sample academic text"""
    print("=== Testing Direct Content Preprocessing ===")
    print()
    
    # Sample academic text (simulating what might come from RAG)
    academic_text = """
    Memory consolidation is a fundamental neurobiological process whereby initially labile memory traces 
    are transformed into more stable, long-term representations through synaptic plasticity mechanisms. 
    During slow-wave sleep, hippocampal sharp-wave ripples coordinate the reactivation of neural ensembles, 
    facilitating the transfer of information from the hippocampus to neocortical regions for permanent storage. 
    This process involves complex molecular cascades including protein synthesis, gene expression changes, 
    and structural modifications at synaptic connections. Research indicates that sleep deprivation significantly 
    impairs consolidation processes, leading to deficits in episodic and declarative memory formation. 
    The timing and duration of sleep stages, particularly non-REM sleep, are critical determinants of 
    consolidation efficiency and subsequent memory retrieval performance.
    """
    
    original_words = len(academic_text.split())
    print(f"Original academic text: {original_words} words")
    print()
    print("Original text:")
    print("-" * 50)
    print(academic_text.strip())
    print("-" * 50)
    print()
    
    # Process the text
    processed_text = preprocess_rag_content(academic_text)
    processed_words = len(processed_text.split()) if processed_text else 0
    
    print(f"Processed text: {processed_words} words")
    print()
    print("Processed text:")
    print("-" * 50)
    print(processed_text)
    print("-" * 50)
    print()
    
    # Analysis
    if processed_words <= 50:
        print(f"SUCCESS: Academic text simplified from {original_words} to {processed_words} words")
    else:
        print(f"WARNING: Text not properly compressed ({original_words} -> {processed_words} words)")
    
    return processed_text


def test_multiple_queries():
    """Test preprocessing with different types of queries"""
    print("=== Testing Multiple Query Types ===")
    print()
    
    queries = [
        "artificial intelligence ethics",
        "brain computer interfaces",
        "privacy digital technology",
        "future memory enhancement"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"Test {i}: {query}")
        print("-" * 30)
        
        try:
            chunks = retrieve_chunks(query)
            processed_content = preprocess_rag_chunks(chunks)
            
            if processed_content:
                word_count = len(processed_content.split())
                print(f"Result: {word_count} words")
                print(f"Content: {processed_content[:150]}...")
            else:
                print("No content generated")
                
        except Exception as e:
            print(f"Failed: {e}")
        
        print()


def main():
    """Run all RAG preprocessor tests"""
    print("RAG Preprocessor Test Suite")
    print("=" * 50)
    print()
    
    # Test 1: Basic retrieval
    chunks = test_rag_retrieval()
    
    # Test 2: Full preprocessing pipeline
    test_rag_preprocessing()
    
    # Test 3: Direct text preprocessing
    test_direct_preprocessing()
    
    # Test 4: Multiple queries
    test_multiple_queries()
    
    print("=" * 50)
    print("Test suite completed")


if __name__ == "__main__":
    main()