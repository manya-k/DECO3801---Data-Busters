"""Constants used across the backend.
"""
import os

OLLAMA_LLM_MODEL_QUESTION = "phi3:3.8b"        # for question generation
OLLAMA_LLM_MODEL_SCENARIO = "qwen3:4b"         # for scenario generation
OLLAMA_LLM_MODEL_IMAGE    = "gemma3:1b-it-qat" # for image text generation
OLLAMA_EMBED_MODEL        = "nomic-embed-text" # for text embedding
OLLAMA_PREPROCESS_MODEL   = "gemma3:1b-it-qat" # for RAG preprocessing

# Legacy constant for backward compatibility
OLLAMA_LLM_MODEL = OLLAMA_LLM_MODEL_QUESTION

# Directory containing RAG vector database files
VECTOR_DB_PATH = os.path.abspath(os.path.join("rag", "db", "faiss_db"))
