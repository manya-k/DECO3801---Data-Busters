#!/usr/bin/env python3
"""
Simplified Memory Editing Scenario Generation Test
Diagnoses why scenario generation always uses fallback content
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'memory_sim.settings')
sys.path.append('/Users/iris/Documents/GitHub/DECO3801---Data-Busters/backend')
django.setup()

from shared.services import (
    generate_and_save_scenario,
    generate_and_save_question
)
from llm.generate import generate_option_descriptions
from llm.prompt_templates import build_description_prompt, build_question_prompt

def test_option_descriptions():
    """Test memory editing scenario description generation"""
    print("=== Memory Editing Scenario Generation Test ===")
    
    # Test parameters - memory editing focused, must be 2 options and 2 context blocks
    year = 2040
    background = "In 2040, global regulations begin piloting clinical memory editing as part of mental health research programs."
    context_blocks = ["consent processes and safety protocols", "clinical trial methodology and oversight"]  # Must be 2
    current_question = "How should memory editing consent procedures be implemented in clinical settings?"
    options = [
        "Establish strict government oversight with mandatory waiting periods", 
        "Allow clinics to self-regulate with professional guidelines"  # Must be 2
    ]
    
    print(f"\nTest Parameters:")
    print(f"- Year: {year}")
    print(f"- Question: {current_question}")
    print(f"- Options count: {len(options)}")
    
    try:
        print("\nStarting option description generation...")
        
        # Call function with correct keyword arguments
        descriptions = generate_option_descriptions(
            year=year,
            background=background,
            context_blocks=context_blocks,
            current_question=current_question,
            options=options
        )
        
        print(f"\nGeneration result type: {type(descriptions)}")
        print(f"Description length: {len(descriptions) if descriptions else 0}")
        
        if descriptions:
            # Parse JSON string
            import json
            try:
                parsed_descriptions = json.loads(descriptions)
                for i, option in enumerate(options):
                    label = chr(65 + i)  # A, B
                    if label in parsed_descriptions:
                        desc_data = parsed_descriptions[label]
                        scenario = desc_data.get('scenario', '')
                        scenario_summary = desc_data.get('scenario_summary', '')
                        query_text = desc_data.get('query_text', '')
                        
                        print(f"\nOption {i+1}: {option}")
                        print(f"Scenario: {scenario[:200]}...")
                        print(f"Word count: {len(scenario.split())} words")
                        print(f"Summary: {scenario_summary}")
                        print(f"Query: {query_text}")
                        
                        # Check if using fallback
                        if "policy-focused approach" in scenario or "research-driven approach" in scenario:
                            print("FALLBACK: Using fallback description") 
                        else:
                            print("SUCCESS: Generated custom description")
                    else:
                        print(f"\nOption {i+1}: {option} - No description found")
            except json.JSONDecodeError:
                print(f"ERROR: Cannot parse JSON result: {descriptions[:100]}...")
        else:
            print("ERROR: No descriptions generated")
            
    except Exception as e:
        print(f"ERROR: Test error occurred: {e}")
        import traceback
        traceback.print_exc()

def test_prompt_generation():
    """Test memory editing prompt generation"""
    print("=== Memory Editing Prompt Generation Test ===")
    
    question = "How should memory editing consent procedures be implemented?"
    selected_option = "Establish strict government oversight with mandatory waiting periods"  
    year = 2040
    background = "In 2040, global regulations begin piloting clinical memory editing as part of mental health research programs."
    
    try:
        # Test description prompt
        prompt = build_description_prompt(
            year=year,
            background=background,
            context_block="consent processes and safety protocols",
            current_question=question,
            selected_option=selected_option
        )
        print(f"Description Prompt Length: {len(prompt)}")
        print(f"Prompt Preview: {prompt[:200]}...")
        
        # Test question prompt
        question_prompt = build_question_prompt(
            year=year,
            background=background,
            context_block="clinical trial methodology and oversight"
        )
        print(f"Question Prompt Length: {len(question_prompt)}")
        print(f"Question Prompt Preview: {question_prompt[:200]}...")
        
    except Exception as e:
        print(f"ERROR: Prompt generation error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("MemorySim Scenario Generation Diagnostic Test")
    print("=" * 60)
    test_prompt_generation()
    test_option_descriptions()#!/usr/bin/env python3
"""
Simplified Memory Editing Scenario Generation Test
Diagnoses why scenario generation always uses fallback content
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'memory_sim.settings')
sys.path.append('/Users/iris/Documents/GitHub/DECO3801---Data-Busters/backend')
django.setup()

from shared.services import (
    generate_and_save_scenario,
    generate_and_save_question
)
from llm.generate import generate_option_descriptions
from llm.prompt_templates import build_description_prompt, build_question_prompt

def test_option_descriptions():
    """Test memory editing scenario description generation"""
    print("=== Memory Editing Scenario Generation Test ===")
    
    # Test parameters - memory editing focused, must be 2 options and 2 context blocks
    year = 2040
    background = "In 2040, global regulations begin piloting clinical memory editing as part of mental health research programs."
    context_blocks = ["consent processes and safety protocols", "clinical trial methodology and oversight"]  # Must be 2
    current_question = "How should memory editing consent procedures be implemented in clinical settings?"
    options = [
        "Establish strict government oversight with mandatory waiting periods", 
        "Allow clinics to self-regulate with professional guidelines"  # Must be 2
    ]
    
    print(f"\nTest Parameters:")
    print(f"- Year: {year}")
    print(f"- Question: {current_question}")
    print(f"- Options count: {len(options)}")
    
    try:
        print("\nStarting option description generation...")
        
        # Call function with correct keyword arguments
        descriptions = generate_option_descriptions(
            year=year,
            background=background,
            context_blocks=context_blocks,
            current_question=current_question,
            options=options
        )
        
        print(f"\nGeneration result type: {type(descriptions)}")
        print(f"Description length: {len(descriptions) if descriptions else 0}")
        
        if descriptions:
            # Parse JSON string
            import json
            try:
                parsed_descriptions = json.loads(descriptions)
                for i, option in enumerate(options):
                    label = chr(65 + i)  # A, B
                    if label in parsed_descriptions:
                        desc_data = parsed_descriptions[label]
                        scenario = desc_data.get('scenario', '')
                        scenario_summary = desc_data.get('scenario_summary', '')
                        query_text = desc_data.get('query_text', '')
                        
                        print(f"\nOption {i+1}: {option}")
                        print(f"Scenario: {scenario[:200]}...")
                        print(f"Word count: {len(scenario.split())} words")
                        print(f"Summary: {scenario_summary}")
                        print(f"Query: {query_text}")
                        
                        # Check if using fallback
                        if "policy-focused approach" in scenario or "research-driven approach" in scenario:
                            print("FALLBACK: Using fallback description") 
                        else:
                            print("SUCCESS: Generated custom description")
                    else:
                        print(f"\nOption {i+1}: {option} - No description found")
            except json.JSONDecodeError:
                print(f"ERROR: Cannot parse JSON result: {descriptions[:100]}...")
        else:
            print("ERROR: No descriptions generated")
            
    except Exception as e:
        print(f"ERROR: Test error occurred: {e}")
        import traceback
        traceback.print_exc()

def test_prompt_generation():
    """Test memory editing prompt generation"""
    print("=== Memory Editing Prompt Generation Test ===")
    
    question = "How should memory editing consent procedures be implemented?"
    selected_option = "Establish strict government oversight with mandatory waiting periods"  
    year = 2040
    background = "In 2040, global regulations begin piloting clinical memory editing as part of mental health research programs."
    
    try:
        # Test description prompt
        prompt = build_description_prompt(
            year=year,
            background=background,
            context_block="consent processes and safety protocols",
            current_question=question,
            selected_option=selected_option
        )
        print(f"Description Prompt Length: {len(prompt)}")
        print(f"Prompt Preview: {prompt[:200]}...")
        
        # Test question prompt
        question_prompt = build_question_prompt(
            year=year,
            background=background,
            context_block="clinical trial methodology and oversight"
        )
        print(f"Question Prompt Length: {len(question_prompt)}")
        print(f"Question Prompt Preview: {question_prompt[:200]}...")
        
    except Exception as e:
        print(f"ERROR: Prompt generation error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("MemorySim Scenario Generation Diagnostic Test")
    print("=" * 60)
    test_prompt_generation()
    test_option_descriptions()