"""
Test script for generate_option_descriptions function.

This script tests the new function that generates descriptions for both options
instead of just the selected one.
"""

import json
import time
from generate import generate_option_descriptions

def test_option_descriptions():
    """Test the generate_option_descriptions function with sample data."""
    
    print("=== Testing generate_option_descriptions Function ===\n")
    
    # Sample test data
    test_data = {
        "year": 2030,
        "background": "In a world where memory editing technology has become widespread, society faces unprecedented ethical and practical challenges.",
        "context_block": "Recent studies show that memory editing can help treat PTSD and depression, but concerns about identity manipulation and consent have emerged. Government agencies are developing regulatory frameworks while tech companies push for innovation.",
        "last_description": "The memory editing debate has reached a critical juncture as various stakeholders prepare to make decisions that will shape the future of human consciousness.",
        "current_question": "How should society approach the regulation of memory editing technology?",
        "options": [
            "Implement strict government oversight with comprehensive licensing requirements",
            "Allow market-driven development with minimal regulatory interference"
        ]
    }
    
    print("Test Parameters:")
    print(f"Year: {test_data['year']}")
    print(f"Background: {test_data['background'][:100]}...")
    print(f"Question: {test_data['current_question']}")
    print(f"Options: {len(test_data['options'])} options provided")
    print("\n" + "="*60 + "\n")
    
    try:
        # Call the function with timing
        print("Calling generate_option_descriptions...")
        start_time = time.time()
        
        results_json = generate_option_descriptions(
            year=test_data["year"],
            background=test_data["background"],
            context_block=test_data["context_block"],
            last_description=test_data["last_description"],
            current_question=test_data["current_question"],
            options=test_data["options"]
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"[SUCCESS] Function call successful!")
        print(f"[TIMING] Execution time: {execution_time:.2f} seconds ({execution_time:.1f}s)\n")
        
        # Parse JSON result
        results = json.loads(results_json)
        print(f"Result type: {type(results_json)} -> {type(results)}")
        
        # Display results for each option
        for label in ['A', 'B']:
            if label in results:
                result = results[label]
                print(f"OPTION {label} RESULT:")
                print(f"Original Option: {test_data['options'][ord(label) - ord('A')]}")
                print("\nGenerated Scenario:")
                scenario = result.get("scenario", "")
                if scenario and isinstance(scenario, str):
                    word_count = len(scenario.split())
                    print(f"  Word Count: {word_count}")
                    print(f"  Content: {scenario}")
                else:
                    print("  [ERROR] Invalid scenario format")
                
                print(f"\nQuery Text: {result.get('query_text', 'N/A')}")
                print("\n" + "-"*50 + "\n")
            else:
                print(f"[ERROR] Missing result for option {label}")
        
        # Validation checks
        print("VALIDATION RESULTS:")
        
        # Check if all options are present
        expected_labels = {'A', 'B'}
        actual_labels = set(results.keys())
        if actual_labels == expected_labels:
            print("[PASS] Both options generated successfully")
        else:
            missing = expected_labels - actual_labels
            extra = actual_labels - expected_labels
            if missing:
                print(f"[FAIL] Missing options: {missing}")
            if extra:
                print(f"[WARN] Extra options: {extra}")
        
        # Check scenario structure for each option
        scenario_valid = True
        for label, result in results.items():
            scenario = result.get("scenario", "")
            if not isinstance(scenario, str):
                print(f"[FAIL] Option {label}: scenario is not a string")
                scenario_valid = False
            elif not scenario.strip():
                print(f"[FAIL] Option {label}: scenario is empty")
                scenario_valid = False
            else:
                # Check word count for the paragraph
                word_count = len(scenario.split())
                if not (80 <= word_count <= 150):
                    print(f"[FAIL] Option {label}: paragraph has {word_count} words, expected 80-150")
                    scenario_valid = False
            
            if not result.get("query_text"):
                print(f"[FAIL] Option {label}: missing query_text")
                scenario_valid = False
        
        if scenario_valid:
            print("[PASS] All scenarios have correct structure (1 paragraph with 80-150 words + query_text)")
        
        # Check for uniqueness
        all_scenarios = []
        all_queries = []
        for result in results.values():
            # Each scenario is now a single paragraph string
            scenario_text = result.get("scenario", "")
            all_scenarios.append(scenario_text)
            all_queries.append(result.get("query_text", ""))
        
        if len(set(all_scenarios)) == 2:
            print("[PASS] Both scenarios are unique")
        else:
            print("[WARN] Scenarios might be duplicated")
        
        if len(set(all_queries)) == 2:
            print("[PASS] Both query texts are unique")
        else:
            print("[WARN] Query texts might be duplicated")
            
        print(f"\nSUMMARY:")
        print(f"Total options processed: {len(results)}/2")
        
        total_words = 0
        valid_scenarios = 0
        for result in results.values():
            scenario = result.get("scenario", "")
            if scenario and isinstance(scenario, str):
                total_words += len(scenario.split())
                valid_scenarios += 1
        
        if valid_scenarios > 0:
            avg_words = total_words / valid_scenarios
            print(f"Average scenario length: {avg_words:.1f} words")
        else:
            print("Average scenario length: N/A (no valid scenarios)")
            
        print(f"Total execution time: {execution_time:.2f} seconds")
        print(f"Average time per option: {execution_time/2:.2f} seconds")
        print(f"Function execution: SUCCESS")
        
    except Exception as e:
        print(f"[ERROR] ERROR during function call:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Function execution: FAILED")

if __name__ == "__main__":
    test_option_descriptions()
