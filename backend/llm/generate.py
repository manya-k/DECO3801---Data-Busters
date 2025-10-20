"""
LLM Generation Module for MemorySim

This module provides functions to generate questions and descriptions using Ollama API
for the MemorySim narrative game. It handles JSON validation, retries, and error handling.
"""

import requests
import json
import re
import logging
from typing import Dict, Any, Union

# Set up logger
logger = logging.getLogger(__name__)

# Handle imports for both relative (Django) and absolute (standalone) usage
try:
    from .prompt_templates import build_question_prompt, build_description_prompt, build_image_text_prompt
    from ..shared.constants import (
        OLLAMA_LLM_MODEL_QUESTION, 
        OLLAMA_LLM_MODEL_SCENARIO, 
        OLLAMA_LLM_MODEL_IMAGE,
        OLLAMA_LLM_MODEL  # for backward compatibility
    )
except ImportError:
    from llm.prompt_templates import build_question_prompt, build_description_prompt, build_image_text_prompt
    from shared.constants import (
        OLLAMA_LLM_MODEL_QUESTION, 
        OLLAMA_LLM_MODEL_SCENARIO, 
        OLLAMA_LLM_MODEL_IMAGE,
        OLLAMA_LLM_MODEL  # for backward compatibility
    )

# Configuration constants
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = OLLAMA_LLM_MODEL  # Default model for backward compatibility

# JSON Schemas for structured output
QUESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {
            "type": "string", 
            "description": "18-35 words written as 2-3 short sentences, with one question mark at the end"
        },
        "options": {
            "type": "array",
            "items": {
                "type": "string",
                "description": "15-30 words, concrete policy/action, mutually exclusive"
            },
            "minItems": 2,
            "maxItems": 2,
            "description": "Exactly 2 option strings"
        },
        "option_queries": {
            "type": "array",
            "items": {
                "type": "string",
                "description": "3–6 lowercase keywords for retrieval (no verbs, no questions)"
            },
            "minItems": 2,
            "maxItems": 2,
            "description": "Exactly 2 RAG queries, one for each option"
        }
    },
    "required": ["question", "options", "option_queries"]
}

DESCRIPTION_SCHEMA = {
    "type": "object",
    "properties": {
        "scenario": {
            "type": "string",
            "description": "Single paragraph with 6-9 short sentences, 80-150 words total"
        },
        "scenario_summary": {
            "type": "string",
            "description": "Brief 20-30 word summary"
        },
        "query_text": {
            "type": "string",
            "description": "Declarative keyword phrase"
        }
    },
    "required": ["scenario", "scenario_summary", "query_text"]
}

OPTIONS_REFINE_SCHEMA = {
    "type": "object",
    "properties": {
        "options": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 2,
            "maxItems": 2,
            "description": "Exactly 2 refined option strings"
        }
    },
    "required": ["options"]
}


# ---------- Shared helpers ----------

def call_ollama(prompt: str, json_schema: dict = None, model: str = None) -> dict:
    """
    Call the Ollama API with the given prompt and return parsed JSON response.
    
    Args:
        prompt: The prompt to send to the model
        json_schema: Optional JSON schema to enforce response format
        model: Optional model name to use (defaults to MODEL constant)
        
    Returns:
        dict: Parsed JSON response from the model
        
    Raises:
        requests.RequestException: If the API call fails
        json.JSONDecodeError: If the response is not valid JSON
    """
    selected_model = model if model else MODEL
    payload = {
        "model": selected_model, 
        "prompt": prompt, 
        "stream": False, 
        "format": json_schema if json_schema else "json",
        "options": {
            "temperature": 0.6,      # Low temperature for more predictable output
            "top_p": 0.95,           # Nucleus sampling
            "top_k": 80,            # Top-k sampling  
            "repeat_penalty": 1.1,  # Penalize repetition
        }
    }
    
    response = requests.post(OLLAMA_URL, json=payload, timeout=60)
    response.raise_for_status()
    
    data = response.json()  # Ollama's response wrapper
    
    # Try to get response from different fields (Ollama versions may vary)
    text = data.get("response", "").strip()
    if not text and "thinking" in data:
        text = data.get("thinking", "").strip()
    
    if not text:
        raise ValueError(f"Empty response from Ollama. Full response: {data}")
    
    return json.loads(text)  # Convert to Python dict


# ---------- Light validators ----------


def validate_question_options(result: dict) -> bool:
    """
    Validate that question result has exactly two valid options.
    
    Args:
        result: The question generation result to validate
        
    Returns:
        bool: True if options are valid, False otherwise
    """
    # Check if options key exists and is a list
    if "options" not in result or not isinstance(result["options"], list):
        return False
    
    options = result.get("options", [])
    
    # Must be exactly 2 options (A, B)
    if len(options) != 2:
        return False
    
    # Each option must be a string with 6-35 words
    for opt in options:
        if not isinstance(opt, str) or not (6 <= len(opt.split()) <= 35):
            return False
        
        # Check for invalid "keywords" content (case insensitive)
        if "keywords" in opt.lower() or "queries" in opt.lower():
            print(f"Validation failed: Option contains 'keywords' or 'queries': {opt}")
            return False

        # Check if the sentence starts with a capital letter or digit
        if not (opt[0].isupper() or opt[0].isdigit()):
            print(f"Validation failed: Option does not start with a capital letter or digit: {opt}")
            return False

    return True


def validate_description_scenario(result: dict) -> bool:
    """
    Validate that description result has correct scenario format and word count.
    
    Args:
        result: The description generation result to validate
        
    Returns:
        bool: True if scenario is valid, False otherwise
    """
    scenario = result.get("scenario", "")
    
    if not isinstance(scenario, str):
        print(f"Validation failed: scenario is not a string, got {type(scenario)}")
        return False
    
    if not scenario.strip():
        print(f"Validation failed: scenario is empty")
        return False
    
    # Check word count
    word_count = len(scenario.split())
    if not (50 <= word_count <= 180):
        print(f"Validation failed: word count is {word_count}, expected 50-180")
        return False
    
    return True


def refine_question_options(original_result: dict) -> dict:
    """
    Attempt to fix invalid options by regenerating only the options array.
    
    Args:
        original_result: The original question result with invalid options
        
    Returns:
        dict: Updated result with refined options
    """
    question = original_result.get("question", "")
    fix_prompt = f"""
   <|system|>

    ROLE
    You are a storyteller for a turn-based museum game about the future of memory technology.
    You previously produced a question but did not provide exactly two valid options.
    Rewrite two opposite mini-story option sentences with the REQUIRED STRUCTURE: "[WHICH GROUP] should [ACTION] so that [RESULT]" with natural language only.
    and do NOT repeat the question text.

    Output schema:
    {{
        "options": [
            "Option A",
            "Option B"
        ]
    }}
    <|end|>
    <|user|>
    Question: {question}
    <|end|>
    <|assistant|>
    """.strip()

    try:
        refined_result = call_ollama(fix_prompt, OPTIONS_REFINE_SCHEMA, model=OLLAMA_LLM_MODEL_QUESTION)
        if validate_question_options(refined_result):
            original_result["options"] = refined_result["options"]
    except Exception as e:
        print(f"Failed to refine options: {e}")
    
    return original_result


def validate_image_texts(image_texts: Dict[str, str]) -> bool:
    """
    Validate that exactly 2 unique non-empty string image texts are generated.
    
    Args:
        image_texts: Dictionary mapping option labels to image descriptions
        
    Returns:
        bool: True if valid (2 unique non-empty strings), False otherwise
    """
    if not isinstance(image_texts, dict):
        return False
    
    # Should have exactly 2 options
    if len(image_texts) != 2:
        return False
    
    # Should have labels A, B
    expected_labels = {'A', 'B'}
    if set(image_texts.keys()) != expected_labels:
        return False
    
    # All image texts should be non-empty strings
    for label, text in image_texts.items():
        if not text or not isinstance(text, str) or not text.strip():
            return False
    
    # All image texts should be unique (no duplicates)
    texts = [text.strip() for text in image_texts.values()]
    if len(set(texts)) != 2:
        return False
    
    return True

# ---------- Story State Management ----------

def create_story_state(
    scenario_summary: str = ""
) -> dict:
    """
    Create a story state with historical context for better narrative continuity.
    
    Args:
        scenario_summary: Summary of the current turn's scenario and theme development
        
    Returns:
        dict: Story state with historical tracking for LLM processing
    """
    return {
        "history": [scenario_summary] if scenario_summary else []
    }


def update_story_state(
    current_state: dict,
    new_scenario_summary: str
) -> dict:
    """
    Update story state with new scenario, maintaining last 50 rounds of history.
    
    Args:
        current_state: Existing story state dict
        new_scenario_summary: New scenario summary and theme development
        
    Returns:
        dict: Updated story state with historical context (max 50 rounds)
    """
    # Get existing history or initialize empty list
    history = current_state.get("history", [])
    
    # Add new scenario summary
    history.append(new_scenario_summary)
    
    # Keep only the last 50 rounds for efficient processing
    if len(history) > 50:
        history = history[-50:]
    
    return {
        "history": history
    }

# ---------- Public API ----------

def generate_question(
    *,
    year: int,
    background: str,
    context_block: str,
    story_state: dict = None,
    max_retries: int = 3,
) -> str:
    """
    Generate a question with two options using the Ollama API and return as JSON string for database storage.
    
    This function creates a decision point in the narrative by generating a question
    with exactly two mutually exclusive options that advance the story.
    
    Args:
        year: The current year in the story timeline (2035 = first year, uses background directly)
        background: The overall story background/setting
        context_block: Retrieved context information for grounding
        story_state: Optional compressed story state (dict with key context for years > 2035)
        max_retries: Maximum number of retry attempts for validation
        
    Returns:
        str: JSON string ready for database storage with keys:
            - question: The generated question
            - options: List of exactly two option strings
            - option_queries: List of two RAG queries, one for each option
            
    Raises:
        Exception: If generation fails after all retries
    """
    print(f"[DEBUG] generate_question CALLED with year={year}, story_state={'present' if story_state else 'None'}")
    logger.info(f"generate_question CALLED with year={year}, story_state={'present' if story_state else 'None'}")
    
    # Year-based validation and context selection
    if year == 2035:
        # First year: use background directly without story state
        logger.info(f"Year {year}: Using first year logic (no story_state)")
        prompt = build_question_prompt(
            year, background, context_block
        )
    elif story_state:
        # Subsequent years with story state: use all historical context
        history = story_state.get("history", [])
        logger.info(f"Year {year}: Using story_state with {len(history)} history entries")
        
        # Build compressed context with all history and RAG content
        if history:
            history_context = "\n".join([f"Turn {i+1}: {summary}" for i, summary in enumerate(history)])
            compressed_context = f"Story History:\n{history_context}\n\nRAG Context: {context_block}"
            logger.info(f"Year {year}: Built compressed context with history ({len(history_context)} chars)")
        else:
            compressed_context = f"RAG Context: {context_block}"
            logger.info(f"Year {year}: story_state exists but history is empty, using RAG only")
            
        prompt = build_question_prompt(
            year, background, compressed_context
        )
    else:
        # Fallback for subsequent years without story state
        logger.info(f"Year {year}: No story_state provided, using fallback context")
        prompt = build_question_prompt(
            year, background, context_block
        )
    
    # Step A: Main generation attempt
    try:
        result = call_ollama(prompt, QUESTION_SCHEMA, model=OLLAMA_LLM_MODEL_QUESTION)

        # Fix question if it doesn't end with question mark
        if 'result' in locals() and 'question' in result:
            question = result.get("question", "").strip()
            if not question.endswith("?"):
                result["question"] = question + " What should we do?"

        if validate_question_options(result):
            return json.dumps(result)
    except Exception as e:
        print(f"Initial question generation failed: {e}")
    
    # Step B: Try to refine options if main generation had invalid options
    if 'result' in locals():
        result = refine_question_options(result)
        if validate_question_options(result):
            return json.dumps(result)
    
    # Step C: Retry main generation
    for attempt in range(max_retries):
        try:
            result = call_ollama(prompt, QUESTION_SCHEMA, model=OLLAMA_LLM_MODEL_QUESTION)

            # Fix question if it doesn't end with question mark
            if 'result' in locals() and 'question' in result:
                question = result.get("question", "").strip()
                if not question.endswith("?"):
                    result["question"] = question + " What should we do?"

            if validate_question_options(result):
                return json.dumps(result)
        except Exception as e:
            print(f"Retry attempt {attempt + 1} failed: {e}")
    
    # Ultimate fallback
    fallback_result = {
        "question": "What should people do about this new technology?",
        "options": [
            "Move forward and try something new",
            "Wait and think more about it first"
        ],
        "option_queries": [
            "new technology and helpful changes",
            "being careful and thinking about problems"
        ]
    }
    return json.dumps(fallback_result)


def generate_option_image_texts(
    *,
    year: int,
    background: str,
    last_description: str,
    question: str,
    options: list,  # List of 2 option texts
    max_retries: int = 2,
) -> str:
    """
    Generate image descriptions for both options and return as JSON string for database storage.
    
    This function creates visual descriptions for each option that can be used
    for image generation, allowing users to preview what each choice might lead to.
    
    Args:
        year: The current year in the story timeline
        background: The overall story background/setting
        last_description: Previous story summary/description
        question: The current question being asked
        options: List of exactly 2 option texts [A, B]
        max_retries: Maximum number of retry attempts for each option
        
    Returns:
        str: JSON string ready for database storage, mapping option labels ('A', 'B') to image descriptions
        
    Raises:
        ValueError: If options list doesn't contain exactly 2 items
    """
    if len(options) != 2:
        raise ValueError(f"Expected exactly 2 options, got {len(options)}")
    
    option_labels = ['A', 'B']
    image_texts = {}
    
    # Default fallback descriptions for each option type
    fallback_descriptions = [
        "People in suits sitting around a big table talking about new rules",
        "Scientists in white coats looking at computers and books in a lab"
    ]
    
    for i, (label, option_text) in enumerate(zip(option_labels, options)):
        success = False
        
        for attempt in range(max_retries):
            try:
                prompt = build_image_text_prompt(
                    year=year,
                    background=background,
                    last_description=last_description,
                    question=question,
                    option_text=option_text
                )
                
                # Create a simple JSON schema for single image description
                single_image_schema = {
                    "type": "object",
                    "properties": {
                        "description": {
                            "type": "string",
                            "description": "Single image description text"
                        }
                    },
                    "required": ["description"]
                }
                
                # Use JSON-based call for individual image descriptions
                result = call_ollama(prompt, single_image_schema, model=OLLAMA_LLM_MODEL_IMAGE)
                
                # Extract the description from JSON result
                if result and "description" in result and len(result["description"]) > 5:
                    image_texts[label] = result["description"]
                    success = True
                    break
                else:
                    print(f"Option {label} attempt {attempt + 1}: Generated description too short or empty")
                    
            except Exception as e:
                print(f"Option {label} attempt {attempt + 1}: Generation failed - {e}")
        
        # Use fallback if all attempts failed
        if not success:
            image_texts[label] = fallback_descriptions[i]
            print(f"Option {label}: Using fallback description")
    
    # Final validation to ensure 2 unique descriptions
    if not validate_image_texts(image_texts):
        print("Generated image texts failed validation, using fallbacks")
        image_texts = {
            'A': fallback_descriptions[0],
            'B': fallback_descriptions[1]
        }
    
    # Always return JSON string for database storage
    return json.dumps(image_texts)


def generate_option_descriptions(
    *,
    year: int,
    background: str,
    context_blocks: list,
    current_question: str,
    options: list,
    story_state: dict = None,
    max_retries: int = 2,
) -> str:
    """
    Generate story descriptions for both options and return as JSON string for database storage.
    
    This function creates different narrative outcomes for each possible choice,
    allowing users to explore the consequences of each option.
    
    Args:
        year: The current year in the story timeline (2035 = first year, uses background directly)
        background: The overall story background/setting
        context_blocks: List of 2 context blocks, each corresponding to one option's RAG query
        current_question: The question that was presented to the player
        options: List of exactly 2 option texts [A, B]
        story_state: Optional compressed story state (dict with key context for years > 2035)
        max_retries: Maximum number of retry attempts for each option
        
    Returns:
        str: JSON string ready for database storage, mapping option labels ('A', 'B') 
        to description results, each containing:
            - scenario: String paragraph (70-120 words)
            - scenario_summary: Brief summary for story state tracking
            - query_text: RAG query string for next turn
            
    Raises:
        ValueError: If options or context_blocks lists don't contain exactly 2 items
    """
    if len(options) != 2:
        raise ValueError(f"Expected exactly 2 options, got {len(options)}")
    
    if len(context_blocks) != 2:
        raise ValueError(f"Expected exactly 2 context blocks, got {len(context_blocks)}")
    
    option_labels = ['A', 'B']
    option_descriptions = {}
    
    # Default fallback descriptions for each option type
    fallback_scenarios = [
        # Option A fallback
        "The government decides to make new rules about the technology. Important people meet in big buildings to talk about what should be allowed and what should not be allowed. They write down the rules on paper and tell everyone what they have to do. Some people are happy because the rules help keep everyone safe. Other people are worried because the rules might slow down new discoveries. Everyone is watching to see what happens next. Will the new rules help people, or will they make things too hard?",
        # Option B fallback
        "Scientists want to learn more before making big decisions. They do lots of experiments and tests to understand how things work. Smart people in labs work together to find out what is safe and what might be dangerous. They write reports about what they discover and share their ideas with everyone. Some people think this is smart because they want to know all the facts first. Other people are getting impatient because they want answers right now. How long will everyone wait before something big happens?"
    ]
    
    fallback_queries = [
        "new rules and government decisions",
        "science experiments and learning more"
    ]
    
    # Process context_block with story_state for each option
    for i, (label, option_text, context_block) in enumerate(zip(option_labels, options, context_blocks)):
        success = False
        
        # Process context_block with story state
        if year == 2035:
            processed_context = context_block
            print(f"[DEBUG] Option {label} Year {year}: Using basic context (first year)")
        elif story_state:
            history = story_state.get("history", [])
            if history:
                history_context = "\n".join([f"Turn {i+1}: {summary}" for i, summary in enumerate(history)])
                processed_context = f"Story History:\n{history_context}\n\nRAG Context: {context_block}"
                print(f"[DEBUG] Option {label} Year {year}: Using story_state with {len(history)} history entries")
            else:
                processed_context = f"RAG Context: {context_block}"
                print(f"[DEBUG] Option {label} Year {year}: story_state exists but history is empty")
        else:
            # Fallback
            processed_context = context_block
            print(f"[DEBUG] Option {label} Year {year}: No story_state provided, using fallback")
        
        for attempt in range(max_retries):
            try:
                prompt = build_description_prompt(
                    year=year,
                    background=background,
                    context_block=processed_context,
                    current_question=current_question,
                    selected_option=option_text
                )
                
                result = call_ollama(prompt, DESCRIPTION_SCHEMA, model=OLLAMA_LLM_MODEL_SCENARIO)
                
                if validate_description_scenario(result):
                    option_descriptions[label] = result
                    success = True
                    break
                else:
                    print(f"Option {label} attempt {attempt + 1}: Scenario validation failed")
                    
            except Exception as e:
                print(f"Option {label} attempt {attempt + 1}: Generation failed - {e}")
        
        # Use fallback if all attempts failed
        if not success:
            option_descriptions[label] = {
                "scenario": fallback_scenarios[i],
                "scenario_summary": f"{'Government makes new rules and people follow them' if i == 0 else 'Scientists do more tests to learn what is safe'} as things keep changing",
                "query_text": fallback_queries[i]
            }
            print(f"Option {label}: Using fallback description")
    
    # Always return JSON string for database storage
    return json.dumps(option_descriptions)
