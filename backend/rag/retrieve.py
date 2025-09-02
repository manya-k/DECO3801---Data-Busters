"""Retrieval logic for the RAG system."""

import logging

from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS

from shared.constants import OLLAMA_EMBED_MODEL, DB_PATH
from shared.utils import get_ollama_embeddings
from rag.setup import setup

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Number of chunks to retrieve per query
NUM_CHUNKS_PER_QUERY = 6

# setup()
# embeddings = get_ollama_embeddings()

# logger.debug(f"Loading vector store from {DB_PATH}...")
# persisted_vectorstore = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)

# # Create a retriever
# logger.debug("Creating retriever from vector store...")
# retriever = persisted_vectorstore.as_retriever(search_kwargs={"k": NUM_CHUNKS_PER_QUERY})  # Retrieve top N documents


def retrieve_chunks(query: str) -> list[dict]:
    """Retrieve relevant chunks from the vector store based on the query."""
    
    logger.info(f"Searching for the query: '{query}'\n")

    retrieved_documents = retriever.invoke(query)

    return [
        {
            "text": doc.page_content,
            "meta": {
                "title": doc.metadata.get("article_title", "Unknown Title")
            }
        }
        for doc in retrieved_documents
    ]
