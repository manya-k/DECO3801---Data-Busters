#!/usr/bin/env python3
# cd /Users/iris/Documents/GitHub/DECO3801---Data-Busters/backend
# python llm/test_rag_integration.py
"""Test complete integration between RAG and LLM systems"""

import sys
import os
import django
import json
import logging

logging.getLogger().setLevel(logging.ERROR)
logging.getLogger('rag').setLevel(logging.ERROR)
logging.getLogger('shared').setLevel(logging.ERROR)
logging.getLogger('httpcore').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('faiss').setLevel(logging.ERROR)

# Django setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'memory_sim.settings')
django.setup()

from rag.retrieve import retrieve_chunks
from llm.generate import generate_question, generate_description
from llm.rag_adapter import get_rag_context, format_rag_context_for_llm


def test_rag_retrieval():
    """Test RAG document retrieval functionality"""
    print("Testing RAG document retrieval...")
    query = "memory consolidation sleep"
    
    try:
        chunks = retrieve_chunks(query)
        print(f"Successfully retrieved {len(chunks)} relevant document chunks")
        
        # Show brief info for first 2 results only
        for i, chunk in enumerate(chunks[:2]):
            title = chunk.get('meta', {}).get('title', 'Unknown')
            content_preview = chunk.get('text', '')[:100] + "..."
            print(f"   Document {i+1}: {title}")
            print(f"      Preview: {content_preview}")
            
        return chunks
    except Exception as e:
        print(f"RAG retrieval failed: {e}")
        return None


def test_rag_adapter():
    """Test RAG adapter functionality"""
    print("\nTesting RAG adapter...")
    
    try:
        # Generate question
        question_result = generate_question(
            year=2024,
            background="A study about memory and sleep",
            context_block="Research context about sleep and memory",
            last_description="Previous research findings"
        )
        # Parse JSON string to get question text
        parsed_question = json.loads(question_result)
        print(f"LLM generated question: {parsed_question['question']}")
        
        # Use adapter to get RAG context
        rag_context = get_rag_context(question_result)
        print(f"RAG query text: {rag_context}")
        
        # Retrieve relevant documents and format
        chunks = retrieve_chunks(rag_context)
        formatted_context = format_rag_context_for_llm(chunks)
        print(f"Formatted RAG context length: {len(formatted_context)} characters")
        
        return True
    except Exception as e:
        print(f"RAG adapter test failed: {e}")
        return False


def test_full_integration():
    """Test complete RAG-LLM integration workflow"""
    print("\nTesting complete RAG-LLM integration workflow...")
    
    try:
        # 1. Generate question
        print("   Step 1: Generating question...")
        question_result = generate_question(
            year=2024,
            background="Memory research study about sleep and consolidation",
            context_block="Scientific research context",
            last_description="Initial research setup"
        )
        # Parse JSON string to get question text
        parsed_question = json.loads(question_result)
        print(f"      Question: {parsed_question['question']}")
        
        # 2. Get RAG context
        print("   Step 2: Getting RAG context...")
        query_text = get_rag_context(question_result)
        chunks = retrieve_chunks(query_text)
        rag_context = format_rag_context_for_llm(chunks)
        print(f"      RAG context length: {len(rag_context)} characters")
        
        # 3. Generate description based on RAG context
        print("   Step 3: Generating scenario description...")
        description_result = generate_description(
            year=2024,
            background="Memory research study",
            context_block=rag_context,
            last_description="Previous findings",
            current_question="Should policy be influenced by the latest research findings?",
            selected_option="Implement new guidelines for post-sleep activities at clinics"
        )
        # Parse JSON string and check the new paragraph format
        parsed_description = json.loads(description_result)
        scenario = parsed_description['scenario']
        if scenario and isinstance(scenario, str):
            word_count = len(scenario.split())
            print(f"      Generated scenario paragraph with {word_count} words")
            print(f"      Word count validation: {'PASS' if 80 <= word_count <= 150 else 'FAIL'}")
            print(f"      Example scenario: {scenario[:100]}...")
        else:
            print("      Generated invalid scenario format")
        
        print("\nFull integration test successful!")
        return True
        
    except Exception as e:
        print(f"Full integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Starting RAG-LLM integration tests...\n")
    
    # Test RAG retrieval
    chunks = test_rag_retrieval()
    
    if chunks:
        # Test adapter
        adapter_ok = test_rag_adapter()
        
        if adapter_ok:
            # Test full workflow
            integration_ok = test_full_integration()
            
            if integration_ok:
                print("\nAll tests passed! RAG-LLM integration working properly.")
            else:
                print("\nFull integration test failed")
        else:
            print("\nRAG adapter test failed")
    else:
        print("\nRAG retrieval test failed")
