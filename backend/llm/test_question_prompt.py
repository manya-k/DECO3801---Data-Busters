import requests, json, re, time
from prompt_templates import build_question_prompt

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3:3.8b"

# Call the Ollama API with the given prompt and return a JSON response dict
def call_ollama(prompt: str) -> dict:
    start_time = time.time()
    r = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "prompt": prompt, "stream": False, "format": "json"},
        timeout=60
    )
    r.raise_for_status()
    data = r.json()  # Ollama's first JSON
    text = data.get("response", "").strip()  # Only get model output
    end_time = time.time()
    print(f"Generation time: {end_time - start_time:.2f} seconds")
    return json.loads(text)                  # Convert to Python dict

# check valid options and option_queries
def valid_two_options(d: dict) -> bool:
    # Check if options key exists and is a list
    if "options" not in d or not isinstance(d["options"], list):
        return False
    options = d.get("options", [])
    # must be exactly 2 options
    if not options or len(options) != 2:
        return False
    for opt in options:
        if not isinstance(opt, str) or not (6 <= len(opt.split()) <= 14):
            return False
    
    # Check if option_queries key exists and is a list
    if "option_queries" not in d or not isinstance(d["option_queries"], list):
        return False
    option_queries = d.get("option_queries", [])
    # must be exactly 2 queries
    if not option_queries or len(option_queries) != 2:
        return False
    for query in option_queries:
        if not isinstance(query, str) or len(query.strip()) == 0:
            return False
    
    return True

# refine the option
def refine_option_fix(original_json: dict) -> dict:
    # if options are invalid, let the model to re-generate options
    question = original_json.get("question", "")
    fix_prompt = f"""
    Return ONLY valid JSON.

    You previously produced a question but did not provide exactly two valid options.
    Rewrite ONLY the "options" array with EXACTLY TWO concise, mutually exclusive choices (6–14 words each).
    and do NOT repeat the question text.

    Question: {question}

    Output schema:
    {{
        "options": [
            "Option A",
            "Option B"
        ],
        "option_queries": [
            "query for option A",
            "query for option B"
        ]
    }}
    """.strip()

    try:
        d = call_ollama(fix_prompt)
        if valid_two_options(d):
            original_json["options"] = d["options"]
            original_json["option_queries"] = d["option_queries"]
    except Exception as e:
        print("refine_options_fix failed:", e)
    return original_json

# Check option validity before output the results
def ensure_valid_options(prompt: str) -> dict:
    """
    Step A: Main call ollama
    Step B: Check option validity
    Step C: Refine options if invalid
    Step D: Retry the main call again
    Step E: fallback
    """

    # Step A
    out = call_ollama(prompt)
    # Step B
    if valid_two_options(out):
        return out
    # Step C
    out = refine_option_fix(out)
    if valid_two_options(out):
        return out
    # Step D
    try:
        retry_out = call_ollama(prompt)
        if valid_two_options(retry_out):
            return retry_out
    except Exception as e:
        print("retry call failed:", e)
    # Step E
    out["options"] = [
        "Take an action that advances the situation forward",
        "Hold back and reconsider before making a move"
    ]
    out["option_queries"] = [
        "memory editing implementation policies and procedures",
        "memory editing ethical concerns and safety considerations"
    ]
    return out



if __name__ == "__main__":
    prompt = build_question_prompt(
        2035,
        "In 2035, global regulations begin piloting clinical memory editing as part of mental health research.",
        "(1) consent processes require strict multi-factor verification; (2) research reports show both benefits and risks for identity stability. Public debate has intensified as clinics prepare to enroll participants in early programs."
        )
    result = ensure_valid_options(prompt)
    print("Clean JSON:\n", json.dumps(result, ensure_ascii=False, indent=2))
    print("\nQuestion:", result["question"])
    print("Options:", result["options"])
    print("Option Queries:", result["option_queries"])