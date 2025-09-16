import requests, json, re
from prompt_templates import build_description_prompt

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3:3.8b"

# Helper: Validate scenario
def validate_scenario(result):
    """
    Validate that scenario meets requirements:
    - One paragraph string with 80-150 words
    """
    scenario = result.get("scenario", "")
    if not isinstance(scenario, str):
        return False

    if not scenario.strip():
        return False
    
    # Check word count is between 80-150 words
    word_count = len(scenario.split())
    if not (80 <= word_count <= 150):
        print(f"Word count validation failed: {word_count} words (expected 80-150)")
        return False
    
    return True

# Call the Ollama API with the given prompt and return a JSON response dict with retries
def call_ollama(prompt: str, max_retries: int = 3) -> dict:
    for attempt in range(max_retries):
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False, "format": "json"},
            timeout=60
        )
        response.raise_for_status()
        
        data = response.json()  # Ollama's response wrapper
        text = data.get("response", "").strip()  # Extract model output
        
        try:
            result = json.loads(text)  # Convert to Python dict
        except Exception as e:
            print(f"[Attempt {attempt+1}] JSON parse failed:", e)
            continue
        
        # Post-check
        if validate_scenario(result):
            return result
        else:
            print(f"[Attempt {attempt+1}] Scenario validation failed, retrying...")
    
    # If all attempts fail, return the last result (may be invalid)
    return result

# Test description prompt
if __name__ == "__main__":
    print("=== Testing Description Generation ===\n")
    
    prompt = build_description_prompt(
        year=2035,
        background="In 2035, global regulations begin piloting clinical memory editing as part of mental health research.",
        context_block="(1) consent processes require strict multi-factor verification; (2) research reports show both benefits and risks for identity stability.",
        last_description="Public debate has intensified as clinics prepare to enroll participants in early programs.",
        current_question="Should the government allow memory editing for clinical trials?",
        selected_option="The government should allow memory editing for clinical trials with strict safeguards",
    )
    
    print("Calling Ollama API...")
    result = call_ollama(prompt)
    
    print("\n=== RESULTS ===")
    print("Clean JSON:\n", json.dumps(result, ensure_ascii=False, indent=2))
    
    # Additional validation info
    if "scenario" in result and result["scenario"]:
        scenario = result["scenario"]
        word_count = len(scenario.split())
        print(f"\n=== VALIDATION INFO ===")
        print(f"Scenario word count: {word_count} words")
        print(f"Word count valid: {'YES' if 80 <= word_count <= 150 else 'NO'}")
        print(f"Scenario format: {'String paragraph' if isinstance(scenario, str) else 'Invalid format'}")
        if "query_text" in result:
            print(f"Query text length: {len(result['query_text'])} characters")
        print(f"Overall validation: {'PASS' if validate_scenario(result) else 'FAIL'}")