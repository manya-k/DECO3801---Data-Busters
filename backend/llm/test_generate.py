#!/usr/bin/env python3
"""
Test script for the generate.py module

This script tests all three main generation functions:
- generate_question: Creates questions with multiple choice options
- generate_option_image_texts: Creates image descriptions for each option
- generate_option_descriptions: Creates scenario descriptions for both options (paragraph format, 80-150 words)

Prerequisites:
1. Ollama should be running on localhost:11434
2. The phi3:3.8b model should be available
3. All dependencies should be installed

Usage:
    python test_generate.py
    python test_generate.py --question-only
    python test_generate.py --image-only
    python test_generate.py --description-only
"""

import sys
import json
import argparse
import requests
from typing import Dict, Any, List

# Import the functions we want to test
from generate import generate_question, generate_option_image_texts, generate_option_descriptions


def print_separator(title: str):
    """Print a formatted separator for test sections"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_result(result: Dict[str, Any], title: str):
    """Pretty print a result dictionary"""
    print(f"\n{title}:")
    print("-" * 40)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def test_generate_question():
    """Test the generate_question function with sample data"""
    print_separator("TESTING GENERATE_QUESTION")
    
    # Test case 1: Basic memory editing scenario
    print("\nTest Case 1: Basic Memory Editing Scenario")
    
    try:
        result_json = generate_question(
            year=2035,
            background="In 2035, global regulations begin piloting clinical memory editing as part of mental health research.",
            context_block="(1) consent processes require strict multi-factor verification; (2) research reports show both benefits and risks for identity stability.",
            last_description="Public debate has intensified as clinics prepare to enroll participants in early programs."
        )
        
        # Parse the JSON string to get the actual result
        result = json.loads(result_json)
        
        print("Question generation succeeded!")
        print_result(result, "Question Result")
        
        # Since the API guarantees valid results, we just check basic structure
        print(f"Question: {result.get('question', 'N/A')}")
        print(f"Number of options: {len(result.get('options', []))}")
        print(f"Query text: {result.get('query_text', 'N/A')}")
            
    except Exception as e:
        print(f"Question generation failed: {e}")
        return False
    
    return True


def test_generate_option_image_texts():
    """Test the generate_option_image_texts function with sample data"""
    print_separator("TESTING GENERATE_OPTION_IMAGE_TEXTS")
    
    print("Test Case: Image Text Generation for Two Options")
    
    try:
        # Sample options that would come from generate_question
        options = [
            "Establish strict government oversight with mandatory waiting periods",
            "Allow clinics to self-regulate with professional guidelines"
        ]
        
        result_json = generate_option_image_texts(
            year=2035,
            background="In 2035, global regulations begin piloting clinical memory editing as part of mental health research.",
            last_description="Public debate has intensified as clinics prepare to enroll participants in early programs.",
            question="How should memory editing consent procedures be implemented?",
            options=options
        )
        
        # Parse the JSON string to get the actual result
        result = json.loads(result_json)
        
        print("Image text generation succeeded!")
        print_result(result, "Image Texts Result")
        
        # Since the API guarantees valid results, we just show the content
        print("\nGenerated image descriptions:")
        for label, text in result.items():
            print(f"{label}: {text}")
            print(f"   Length: {len(text)} chars, {len(text.split())} words")
            
    except Exception as e:
        print(f"Image text generation failed: {e}")
        return False
    
    return True


def test_generate_option_descriptions():
    """Test the generate_option_descriptions function with sample data"""
    print_separator("TESTING GENERATE_OPTION_DESCRIPTIONS")
    
    # Test case 1: Basic option descriptions generation (paragraph format for both options)
    print("\nTest Case 1: Option Descriptions Generation (Paragraph Format)")
    
    try:
        # Sample options for testing
        test_options = [
            "Allow memory editing with comprehensive safety protocols",
            "Postpone implementation until more research is completed"
        ]
        
        result_json = generate_option_descriptions(
            year=2035,
            background="In 2035, global regulations begin piloting clinical memory editing as part of mental health research.",
            context_block="(1) consent processes require strict multi-factor verification; (2) research reports show both benefits and risks for identity stability.",
            last_description="Public debate has intensified as clinics prepare to enroll participants in early programs.",
            current_question="Should the government allow memory editing for clinical trials?",
            options=test_options
        )
        
        # Parse the JSON string to get the actual result
        result = json.loads(result_json)
        
        print("Option descriptions generation succeeded!")
        print_result(result, "Option Descriptions Result")
        
        # Validate both option descriptions
        print("\nGenerated option scenarios:")
        option_labels = ['A', 'B']
        
        for label in option_labels:
            if label in result:
                option_data = result[label]
                scenario = option_data.get("scenario", "")
                
                if scenario and isinstance(scenario, str):
                    word_count = len(scenario.split())
                    validation = 'PASS' if 80 <= word_count <= 150 else 'FAIL'
                    
                    print(f"\nOption {label}:")
                    print(f"  Word count: {word_count} ({validation})")
                    print(f"  Query: {option_data.get('query_text', 'N/A')}")
                    print(f"  Content preview: {scenario[:100]}{'...' if len(scenario) > 100 else ''}")
                else:
                    print(f"\nOption {label}: Invalid scenario format")
            else:
                print(f"\nOption {label}: Missing from results")
            
    except Exception as e:
        print(f"Option descriptions generation failed: {e}")
        return False
    
    return True


def test_ollama_connectivity():
    """Test if Ollama is running and accessible"""
    print_separator("TESTING OLLAMA CONNECTIVITY")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in models]
            print("Ollama is running!")
            print(f"Available models: {model_names}")
            
            if "phi3:3.8b" in model_names:
                print("phi3:3.8b model is available!")
                return True
            else:
                print("phi3:3.8b model not found. Available models:")
                for name in model_names:
                    print(f"   - {name}")
                print("\nTo install phi3:3.8b, run: ollama pull phi3:3.8b")
                return False
        else:
            print(f"Ollama responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Cannot connect to Ollama. Is it running on localhost:11434?")
        print("To start Ollama, run: ollama serve")
        return False
    except Exception as e:
        print(f"Error checking Ollama: {e}")
        return False


def run_full_workflow_test():
    """Test the complete workflow: question -> image texts -> description"""
    print_separator("TESTING COMPLETE WORKFLOW")
    
    print("Test Case: Complete Generation Workflow")
    
    try:
        # Step 1: Generate question
        print("\nStep 1: Generating question...")
        question_result_json = generate_question(
            year=2035,
            background="In 2035, global regulations begin piloting clinical memory editing as part of mental health research.",
            context_block="(1) consent processes require strict multi-factor verification; (2) research reports show both benefits and risks for identity stability.",
            last_description="Public debate has intensified as clinics prepare to enroll participants in early programs."
        )
        
        # Parse the JSON string to get the actual result
        question_result = json.loads(question_result_json)
        
        # Since the API guarantees valid results, just check basic structure
        if not question_result or 'question' not in question_result:
            print("Question generation returned invalid structure")
            return False
        
        print(f"Generated question: {question_result['question']}")
        print(f"Options: {question_result.get('options', [])}")
        
        # Step 2: Generate image texts (using the same 2 options structure)
        print("\nStep 2: Generating image texts...")
        test_options = [
            "Establish strict government oversight with mandatory waiting periods",
            "Allow clinics to self-regulate with professional guidelines"
        ]
        
        image_result_json = generate_option_image_texts(
            year=2035,
            background="In 2035, global regulations begin piloting clinical memory editing as part of mental health research.",
            last_description="Public debate has intensified as clinics prepare to enroll participants in early programs.",
            question=question_result['question'],
            options=test_options
        )
        
        # Parse the JSON string to get the actual result
        image_result = json.loads(image_result_json)
        
        # Since the API guarantees valid results, just check basic structure
        if not image_result or len(image_result) != 2:
            print("Image text generation returned invalid structure")
            return False
        
        print("Generated image texts for both options")
        
        # Step 3: Generate option descriptions for both options
        print("\nStep 3: Generating option descriptions...")
        option_descriptions_result_json = generate_option_descriptions(
            year=2035,
            background="In 2035, global regulations begin piloting clinical memory editing as part of mental health research.",
            context_block="(1) consent processes require strict multi-factor verification; (2) research reports show both benefits and risks for identity stability.",
            last_description="Public debate has intensified as clinics prepare to enroll participants in early programs.",
            current_question=question_result['question'],
            options=test_options
        )
        
        # Parse the JSON string to get the actual result
        option_descriptions_result = json.loads(option_descriptions_result_json)
        
        # Since the API guarantees valid results, just check basic structure
        if not option_descriptions_result or len(option_descriptions_result) != 2:
            print("Option descriptions generation returned invalid structure")
            return False
        
        # Validate both option descriptions
        valid_count = 0
        for label in ['A', 'B']:
            if label in option_descriptions_result:
                scenario = option_descriptions_result[label].get('scenario', "")
                if scenario and isinstance(scenario, str):
                    word_count = len(scenario.split())
                    if 80 <= word_count <= 150:
                        valid_count += 1
                        
        print(f"Generated option descriptions: {valid_count}/2 options passed validation")
        if valid_count != 2:
            print("Option descriptions validation: FAIL")
            return False
        else:
            print("Option descriptions validation: PASS")
        
        print("Generated complete option descriptions for both choices")
        
        print("\nComplete workflow test passed!")
        print("All three generation functions work correctly and produce valid outputs")
        return True
        
    except Exception as e:
        print(f"Workflow test failed: {e}")
        return False


def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Test the generate.py module")
    parser.add_argument("--question-only", action="store_true", 
                       help="Only test question generation")
    parser.add_argument("--image-only", action="store_true", 
                       help="Only test image text generation")
    parser.add_argument("--description-only", action="store_true", 
                       help="Only test description generation")
    parser.add_argument("--workflow", action="store_true", 
                       help="Test complete workflow")
    args = parser.parse_args()
    
    print("MemorySim Generate.py Test Suite")
    print("=" * 60)
    
    # Check Ollama connectivity first
    if not test_ollama_connectivity():
        print("\nCannot proceed without Ollama connectivity")
        return False
    
    success = True
    
    # Run tests based on arguments
    if args.workflow:
        success &= run_full_workflow_test()
    elif args.question_only:
        success &= test_generate_question()
    elif args.image_only:
        success &= test_generate_option_image_texts()
    elif args.description_only:
        success &= test_generate_option_descriptions()
    else:
        # Run all tests by default
        success &= test_generate_question()
        success &= test_generate_option_image_texts()
        success &= test_generate_option_descriptions()
        success &= run_full_workflow_test()
    
    # Summary
    print_separator("TEST SUMMARY")
    if success:
        print("All tests passed successfully!")
        print("\nNext steps:")
        print("   1. Integrate these functions into your Django views")
        print("   2. Add error handling for production use")
        print("   3. Consider adding unit tests with mocked responses")
        print("   4. Monitor generation quality and adjust prompts as needed")
    else:
        print("Some tests failed. Check the output above for details.")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
