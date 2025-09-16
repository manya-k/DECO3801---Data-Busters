"""
LLM Generation Module for MemorySim

This module provides functions to generate questions and descriptions using Ollama API
for the MemorySim narrative game. It handles JSON validation, retries, and error handling.
"""

import requests
import json
import re
from typing import Dict, Any, Union

# Handle imports for both relative (Django) and absolute (standalone) usage
try:
    from .prompt_templates import build_question_prompt, build_description_prompt, build_image_text_prompt
except ImportError:
    from prompt_templates import build_question_prompt, build_description_prompt, build_image_text_prompt

# Configuration constants
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3:3.8b"

# JSON Schemas for structured output
QUESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "query_text": {
            "type": "string",
            "description": "Declarative keyword phrase for RAG retrieval"
        },
        "question": {
            "type": "string", 
            "description": "The generated question"
        },
        "options": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 4,
            "maxItems": 4,
            "description": "Exactly 4 option strings"
        }
    },
    "required": ["query_text", "question", "options"]
}

DESCRIPTION_SCHEMA = {
    "type": "object",
    "properties": {
        "scenario": {
            "type": "string",
            "description": "Single paragraph with 80-150 words"
        },
        "query_text": {
            "type": "string",
            "description": "Declarative keyword phrase for next turn retrieval"
        }
    },
    "required": ["scenario", "query_text"]
}

OPTIONS_REFINE_SCHEMA = {
    "type": "object",
    "properties": {
        "options": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 4,
            "maxItems": 4,
            "description": "Exactly 4 refined option strings"
        }
    },
    "required": ["options"]
}


# ---------- Shared helpers ----------

def call_ollama(prompt: str, json_schema: dict = None) -> dict:
    """
    Call the Ollama API with the given prompt and return parsed JSON response.
    
    Args:
        prompt: The prompt to send to the model
        json_schema: Optional JSON schema to enforce response format
        
    Returns:
        dict: Parsed JSON response from the model
        
    Raises:
        requests.RequestException: If the API call fails
        json.JSONDecodeError: If the response is not valid JSON
    """
    payload = {
        "model": MODEL, 
        "prompt": prompt, 
        "stream": False, 
        "format": "json"
    }
    
    # Add JSON schema if provided (for better structured output)
    if json_schema:
        payload["format"] = json_schema
    
    response = requests.post(OLLAMA_URL, json=payload, timeout=60)
    response.raise_for_status()
    
    data = response.json()  # Ollama's response wrapper
    text = data.get("response", "").strip()  # Extract model output
    
    return json.loads(text)  # Convert to Python dict


# ---------- Light validators ----------

def validate_question_options(result: dict) -> bool:
    """
    Validate that question result has exactly four valid options.
    
    Args:
        result: The question generation result to validate
        
    Returns:
        bool: True if options are valid, False otherwise
    """
    # Check if options key exists and is a list
    if "options" not in result or not isinstance(result["options"], list):
        return False
    
    options = result.get("options", [])
    
    # Must be exactly 4 options (A, B, C, D)
    if len(options) != 4:
        return False
    
    # Each option must be a string with 6-14 words
    for opt in options:
        if not isinstance(opt, str) or not (6 <= len(opt.split()) <= 14):
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
    
    # Check word count is between 80-150 words
    word_count = len(scenario.split())
    if not (80 <= word_count <= 150):
        print(f"Validation failed: word count is {word_count}, expected 80-150")
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
    Return ONLY valid JSON.

    You previously produced a question but did not provide exactly four valid options.
    Rewrite ONLY the "options" array with EXACTLY FOUR concise, mutually exclusive choices (6–14 words each).
    and do NOT repeat the question text.

    Question: {question}

    Output schema:
    {{
        "options": [
            "Option A",
            "Option B", 
            "Option C",
            "Option D"
        ]
    }}
    """.strip()

    try:
        refined_result = call_ollama(fix_prompt, OPTIONS_REFINE_SCHEMA)
        if validate_question_options(refined_result):
            original_result["options"] = refined_result["options"]
    except Exception as e:
        print(f"Failed to refine options: {e}")
    
    return original_result


def validate_image_texts(image_texts: Dict[str, str]) -> bool:
    """
    Validate that exactly 4 unique non-empty string image texts are generated.
    
    Args:
        image_texts: Dictionary mapping option labels to image descriptions
        
    Returns:
        bool: True if valid (4 unique non-empty strings), False otherwise
    """
    if not isinstance(image_texts, dict):
        return False
    
    # Should have exactly 4 options
    if len(image_texts) != 4:
        return False
    
    # Should have labels A, B, C, D
    expected_labels = {'A', 'B', 'C', 'D'}
    if set(image_texts.keys()) != expected_labels:
        return False
    
    # All image texts should be non-empty strings
    for label, text in image_texts.items():
        if not text or not isinstance(text, str) or not text.strip():
            return False
    
    # All image texts should be unique (no duplicates)
    texts = [text.strip() for text in image_texts.values()]
    if len(set(texts)) != 4:
        return False
    
    return True

# ---------- Public API ----------

def generate_question(
    *,
    year: int,
    background: str,
    context_block: str,
    last_description: str,
    max_retries: int = 3,
) -> str:
    """
    Generate a question with four options using the Ollama API and return as JSON string for database storage.
    
    This function creates a decision point in the narrative by generating a question
    with exactly four mutually exclusive options that advance the story.
    
    Args:
        year: The current year in the story timeline
        background: The overall story background/setting
        context_block: Retrieved context information for grounding
        last_description: Previous story summary/description
        max_retries: Maximum number of retry attempts for validation
        
    Returns:
        str: JSON string ready for database storage with keys:
            - query_text: RAG query for retrieving relevant information
            - question: The generated question
            - options: List of exactly four option strings
            
    Raises:
        Exception: If generation fails after all retries
    """
    prompt = build_question_prompt(
        year, background, context_block, last_description
    )
    
    # Step A: Main generation attempt
    try:
        result = call_ollama(prompt, QUESTION_SCHEMA)
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
            result = call_ollama(prompt, QUESTION_SCHEMA)
            if validate_question_options(result):
                return json.dumps(result)
        except Exception as e:
            print(f"Retry attempt {attempt + 1} failed: {e}")
    
    # Step D: Fallback with default options
    if 'result' in locals():
        result["options"] = [
            "Take an action that advances the situation forward",
            "Hold back and reconsider before making a move",
            "Seek additional information before deciding",
            "Propose an alternative approach to the situation"
        ]
        return json.dumps(result)
    
    # Ultimate fallback
    fallback_result = {
        "query_text": "memory editing ethical considerations",
        "question": "How should society proceed with memory editing technology?",
        "options": [
            "Take an action that advances the situation forward",
            "Hold back and reconsider before making a move", 
            "Seek additional information before deciding",
            "Propose an alternative approach to the situation"
        ]
    }
    return json.dumps(fallback_result)


def generate_option_image_texts(
    *,
    year: int,
    background: str,
    last_description: str,
    question: str,
    options: list,  # List of 4 option texts
    max_retries: int = 2,
) -> str:
    """
    Generate image descriptions for all four options and return as JSON string for database storage.
    
    This function creates visual descriptions for each option that can be used
    for image generation, allowing users to preview what each choice might lead to.
    
    Args:
        year: The current year in the story timeline
        background: The overall story background/setting
        last_description: Previous story summary/description
        question: The current question being asked
        options: List of exactly 4 option texts [A, B, C, D]
        max_retries: Maximum number of retry attempts for each option
        
    Returns:
        str: JSON string ready for database storage, mapping option labels ('A', 'B', 'C', 'D') to image descriptions
        
    Raises:
        ValueError: If options list doesn't contain exactly 4 items
    """
    if len(options) != 4:
        raise ValueError(f"Expected exactly 4 options, got {len(options)}")
    
    option_labels = ['A', 'B', 'C', 'D']
    image_texts = {}
    
    # Default fallback descriptions for each option type
    fallback_descriptions = [
        "Officials in a modern conference room discussing policy implementation",
        "Researchers in a laboratory setting reviewing technical documentation", 
        "Citizens in a public forum space engaged in community discussion",
        "Experts in a consultation room analyzing regulatory frameworks"
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
                result = call_ollama(prompt, single_image_schema)
                
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
    
    # Final validation to ensure 4 unique descriptions
    if not validate_image_texts(image_texts):
        print("Generated image texts failed validation, using fallbacks")
        image_texts = {
            'A': fallback_descriptions[0],
            'B': fallback_descriptions[1], 
            'C': fallback_descriptions[2],
            'D': fallback_descriptions[3]
        }
    
    # Always return JSON string for database storage
    return json.dumps(image_texts)


def generate_option_descriptions(
    *,
    year: int,
    background: str,
    context_block: str,
    last_description: str,
    current_question: str,
    options: list,  # List of 4 option texts
    max_retries: int = 2,
) -> str:
    """
    Generate story descriptions for all four options and return as JSON string for database storage.
    
    This function creates different narrative outcomes for each possible choice,
    allowing users to explore the consequences of each option.
    
    Args:
        year: The current year in the story timeline
        background: The overall story background/setting
        context_block: Retrieved context information for grounding
        last_description: Previous story summary/description
        current_question: The question that was presented to the player
        options: List of exactly 4 option texts [A, B, C, D]
        max_retries: Maximum number of retry attempts for each option
        
    Returns:
        str: JSON string ready for database storage, mapping option labels ('A', 'B', 'C', 'D') 
        to description results, each containing:
            - scenario: String paragraph (80-150 words)
            - query_text: RAG query string for next turn
            
    Raises:
        ValueError: If options list doesn't contain exactly 4 items
    """
    if len(options) != 4:
        raise ValueError(f"Expected exactly 4 options, got {len(options)}")
    
    option_labels = ['A', 'B', 'C', 'D']
    option_descriptions = {}
    
    # Default fallback descriptions for each option type
    fallback_scenarios = [
        # Option A fallback
        "The policy-focused approach creates structured institutional changes as government agencies begin implementing new regulatory frameworks. Official committees meet to establish standardized procedures while public institutions adapt their operations to comply with new guidelines. The systematic approach ensures consistent implementation across all sectors, creating a foundation for regulated progress. Citizens observe these developments with cautious optimism, wondering how these changes will affect their daily lives. What balance between safety and innovation will ultimately emerge from this structured approach?",
        # Option B fallback
        "The research-driven approach prioritizes scientific investigation as scientists launch comprehensive studies to gather empirical data. Research facilities expand their capabilities to support the investigation while academic institutions collaborate to publish findings and recommendations. Evidence-based conclusions guide future decision-making processes, ensuring that policy follows scientific understanding. The methodical pace frustrates some stakeholders who seek immediate solutions, yet others appreciate the thoroughness. How long will society wait for definitive answers before demanding action?",
        # Option C fallback
        "The community-centered approach emphasizes public participation as citizens organize town halls and public forums for discussion. Local communities form committees to represent diverse perspectives while grassroots movements emerge to advocate for community interests. Democratic processes ensure that all voices are heard and considered, creating a foundation of public trust. However, the diversity of opinions sometimes leads to prolonged debates and delayed decisions. Can collective wisdom overcome the challenges of reaching consensus?",
        # Option D fallback
        "The expert consultation approach relies on specialized knowledge as technical specialists convene to analyze complex implications. Professional organizations provide detailed assessments and guidance while industry experts share insights based on practical experience. Specialized knowledge informs strategic planning and implementation, leveraging years of accumulated expertise. Critics worry that expert perspectives may not fully account for public concerns and values. Will technical excellence translate into solutions that serve everyone's needs?"
    ]
    
    fallback_queries = [
        "policy implementation and regulatory frameworks",
        "scientific research and empirical evidence",
        "community engagement and public participation",
        "expert consultation and specialized knowledge"
    ]
    
    for i, (label, option_text) in enumerate(zip(option_labels, options)):
        success = False
        
        for attempt in range(max_retries):
            try:
                prompt = build_description_prompt(
                    year=year,
                    background=background,
                    context_block=context_block,
                    last_description=last_description,
                    current_question=current_question,
                    selected_option=option_text
                )
                
                result = call_ollama(prompt, DESCRIPTION_SCHEMA)
                
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
                "query_text": fallback_queries[i]
            }
            print(f"Option {label}: Using fallback description")
    
    # Always return JSON string for database storage
    return json.dumps(option_descriptions)


def generate_description(
    *,
    year: int,
    background: str,
    context_block: str,
    last_description: str,
    current_question: str,
    selected_option: str,
    max_retries: int = 3,
) -> str:
    """
    Generate a story description based on the selected option and return as JSON string for database storage.
    
    This function creates the next part of the narrative by incorporating the
    player's choice and generating a vivid scenario with accompanying metadata.
    
    Args:
        year: The current year in the story timeline
        background: The overall story background/setting
        context_block: Retrieved context information for grounding
        last_description: Previous story summary/description
        current_question: The question that was presented to the player
        selected_option: The option chosen by the player
        max_retries: Maximum number of retry attempts for validation
        
    Returns:
        str: JSON string ready for database storage with keys:
            - scenario: String paragraph (80-150 words)
            - query_text: RAG query string for next turn
            
    Raises:
        Exception: If generation fails after all retries
    """
    prompt = build_description_prompt(
        year, background, context_block, last_description,
        current_question, selected_option
    )
    
    # Attempt generation with retries
    for attempt in range(max_retries):
        try:
            result = call_ollama(prompt, DESCRIPTION_SCHEMA)
            
            if validate_description_scenario(result):
                return json.dumps(result)
            else:
                print(f"Attempt {attempt + 1}: Scenario validation failed, retrying...")
                
        except Exception as e:
            print(f"Attempt {attempt + 1}: Generation failed - {e}")
    
    # If all attempts fail, return a fallback result
    fallback_result = {
        "scenario": "The selected decision creates immediate ripple effects across institutions and communities as stakeholders gather in meeting rooms and public spaces to discuss the implications of this choice. New policies and procedures begin to take shape based on the direction that was chosen, while citizens and experts alike watch closely as the consequences unfold in real time. The path forward remains uncertain, but the choice has been made and will shape future developments. Implementation challenges emerge as different groups interpret the decision through their own perspectives and priorities. How will society adapt to the changes that this pivotal moment has set in motion?",
        "query_text": "policy implementation and social consequences of memory editing decisions"
    }
    return json.dumps(fallback_result)



