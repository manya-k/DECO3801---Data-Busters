import requests, json, re, os, sys
from prompt_templates import build_image_text_prompt

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3:3.8b"


def clean_ollama_output(text: str) -> str:
    """
    Clean up common issues in Ollama text output
    """
    if not text:
        return text
    
    # Remove leading/trailing quotes
    text = text.strip()
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1].strip()
    
    # Split by lines and clean each
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip lines with unwanted content
        line_lower = line.lower()
        unwanted_patterns = [
            'now let\'s move to',
            'instruction:',
            '---',
            'second much more',
            'difficult instruction',
            'here\'s',
            'let me',
            'i\'ll',
            'this is'
        ]
        
        skip_line = False
        for pattern in unwanted_patterns:
            if pattern in line_lower:
                skip_line = True
                break
        
        if skip_line:
            continue
            
        cleaned_lines.append(line)
    
    # Take the first meaningful line (usually the actual description)
    if cleaned_lines:
        result = cleaned_lines[0]
        
        # Remove any trailing incomplete sentences or meta-text
        sentences = result.split('.')
        if len(sentences) > 1:
            # Keep complete sentences, remove incomplete trailing parts
            complete_sentences = []
            for sentence in sentences[:-1]:  # All but last
                if sentence.strip():
                    complete_sentences.append(sentence.strip())
            
            # Check if last sentence looks complete
            last_sentence = sentences[-1].strip()
            if last_sentence and not any(word in last_sentence.lower() for word in ['instruction', 'now let', 'move to']):
                complete_sentences.append(last_sentence)
            
            if complete_sentences:
                result = '. '.join(complete_sentences)
                if not result.endswith('.'):
                    result += '.'
        
        return result
    
    return text

# Validate individual image text
def valid_image_text(text: str) -> bool:
    """
    Check if generated image text meets basic requirements
    """
    if not text or not isinstance(text, str):
        print("  ✗ Text is empty or not a string")
        return False
    
    text = text.strip()
    
    # Remove quotes if wrapped
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1].strip()
    
    # Check for unwanted instruction text or meta-content
    unwanted_patterns = [
        "now let's move to",
        "instruction:",
        "---",
        "second much more",
        "difficult instruction"
    ]
    text_lower = text.lower()
    for pattern in unwanted_patterns:
        if pattern in text_lower:
            print(f"  ✗ Contains unwanted instruction text: '{pattern}'")
            return False
    
    # Check minimum length and contains spaces (multiple words)
    if len(text) <= 15:
        print(f"  ✗ Too short: {len(text)} chars (need >15)")
        return False
        
    if ' ' not in text:
        print("  ✗ Single word, need multiple words")
        return False
    
    # Check word count (under 75 words as per prompt requirement)
    word_count = len(text.split())
    if word_count > 75:
        print(f"  ✗ Too many words: {word_count} (max 75)")
        return False
    
    # Check character limit (reasonable for image descriptions)
    if len(text) > 400:
        print(f"  ✗ Too long: {len(text)} chars (max 400)")
        return False
    
    # Should contain some visual elements (basic check)
    visual_keywords = [
        'room', 'table', 'screen', 'building', 'office', 'lab', 'hall', 'center', 
        'space', 'area', 'people', 'crowd', 'group', 'officials', 'scientists', 
        'citizens', 'staff', 'researchers', 'conference', 'meeting', 'laboratory',
        'forum', 'consultation', 'government', 'clinic', 'hospital', 'facility',
        'cityscape', 'urban', 'scene', 'environment', 'setting', 'atmosphere',
        'lighting', 'neon', 'futuristic', 'modern', 'professional'
    ]
    
    if not any(keyword in text_lower for keyword in visual_keywords):
        print(f"  ✗ No visual keywords found in: '{text[:50]}...'")
        return False
    
    print(f"  ✓ Valid: {len(text)} chars, {word_count} words")
    return True

# Generate image description with validation and fallbacks


# Test the actual generate_option_image_texts function from generate.py
def test_generate_option_image_texts(
    year: int,
    background: str,
    last_description: str, 
    question: str,
    options: list
) -> dict:
    """
    Test the actual generate_option_image_texts function which returns JSON string
    """
    from generate import generate_option_image_texts
    
    print("Calling actual generate_option_image_texts function...\n")
    
    # Call the actual function (returns JSON string)
    json_result = generate_option_image_texts(
        year=year,
        background=background,
        last_description=last_description,
        question=question,
        options=options
    )
    
    print(f"Function returned type: {type(json_result)}")
    print(f"JSON result: {json_result}")
    print()
    
    # Parse JSON string back to dict for validation and display
    image_texts = json.loads(json_result)
    
    print("Parsed image descriptions:")
    for label, text in image_texts.items():
        print(f"=== Option {label} ===")
        print(f"Generated: {text}")
        print(f"Length: {len(text)} chars, {len(text.split())} words")
        print(f"Valid: {valid_image_text(text)}")
        print()
    
    return image_texts

# Validate final results
def validate_image_texts(image_texts: dict) -> bool:
    """
    Validate that exactly 2 unique image texts are generated
    """
    if not isinstance(image_texts, dict) or len(image_texts) != 2:
        return False
    
    # Should have labels A, B
    expected_labels = {'A', 'B'}
    if set(image_texts.keys()) != expected_labels:
        return False
    
    # All image texts should be valid
    for label, text in image_texts.items():
        if not valid_image_text(text):
            return False
    
    # All image texts should be unique (no duplicates)
    texts = [text.strip() for text in image_texts.values()]
    if len(set(texts)) != 2:
        print("Warning: Some image descriptions are duplicates!")
        return False
    
    return True


if __name__ == "__main__":
    # Test data
    test_year = 2035
    test_background = "In 2035, global regulations begin piloting clinical memory editing as part of mental health research."
    test_last_description = "Public debate has intensified as clinics prepare to enroll participants in early programs."
    test_question = "How should memory editing consent procedures be implemented?"
    test_options = [
        "Establish strict government oversight with mandatory waiting periods",
        "Allow clinics to self-regulate with professional guidelines"
    ]
    
    print("=== Image Text Generation Test ===")
    print(f"Year: {test_year}")
    print(f"Background: {test_background}")
    print(f"Last Description: {test_last_description}")
    print(f"Question: {test_question}")
    print("Options:")
    for i, opt in enumerate(test_options):
        print(f"  {chr(65+i)}: {opt}")
    print("\n" + "="*60 + "\n")
    
    # Generate image descriptions
    try:
        result = test_generate_option_image_texts(
            year=test_year,
            background=test_background,
            last_description=test_last_description,
            question=test_question,
            options=test_options
        )
        
        print("=== FINAL RESULTS ===")
        print("Image descriptions:")
        for label, text in result.items():
            print(f"{label}: {text}")
        
        print(f"\nValidation passed: {validate_image_texts(result)}")
        
        # JSON output for easy copying
        print("\n=== JSON OUTPUT ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"Test failed with error: {e}")
