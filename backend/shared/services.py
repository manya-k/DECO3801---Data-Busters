"""
Business Service Layer for MemorySim

This module provides high-level business logic functions that coordinate between
different components (LLM, RAG, Database) to deliver complete game functionality.

Key Functions:
- generate_and_save_question(): Generate and save questions for new turns
- generate_and_save_scenario(): Generate and save scenario descriptions 
- generate_and_save_image_text(): Generate and save image descriptions
- record_user_choice(): Record player's choice for a turn
- display_world_view(): Display results after player makes a choice
- get_session_status(): Get current session progress information

This service layer handles the complete workflow from content generation 
to database storage, ensuring data consistency and proper error handling.
"""

import json
import logging
from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone

# Import models
from .models import Session, Turn, Option, WorldBackground, DefaultQueryList

# Import LLM generation functions
from llm.generate import generate_question, create_story_state, update_story_state

# Import RAG functionality
from rag.retrieve import retrieve_chunks
from llm.rag_preprocessor import preprocess_rag_chunks
from images.render_pipeline import generate_two_images_blocking

logger = logging.getLogger(__name__)

@transaction.atomic
def generate_and_save_question(session_id: int, year: int) -> Dict[str, Any]:
    """
    Generate a new question for the specified session and year, then save all results to database.
    
    This function orchestrates the complete question generation workflow:
    1. Gather parameters from various data sources
    2. Call LLM generation functions
    3. Parse and save results to database
    
    Args:
        session_id: The game session ID
        year: The target year for question generation
        
    Returns:
        Dict containing the generated question data and database IDs
        
    Raises:
        Session.DoesNotExist: If session not found
        Exception: If generation or database operations fail
    """
    logger.info(f"Starting question generation for session {session_id}, year {year}")
    
    # Step 1: Get session and world background
    try:
        session = Session.objects.get(id=session_id)
        logger.debug(f"Retrieved session {session_id}")
    except Session.DoesNotExist:
        logger.error(f"Session {session_id} not found")
        raise
    
    try:
        world_background = WorldBackground.objects.first()  # Get the first/default background
        background = world_background.content if world_background else ""
        logger.debug(f"Retrieved world background with length: {len(background)}")
    except Exception as e:
        logger.warning(f"Failed to retrieve world background: {e}")
        background = ""  # Use empty string as fallback
    
    # Step 2: Get RAG context from previous turn or default keywords
    context_block = ""
    
    if year > 2035:  # Not the first turn
        try:
            previous_turn = Turn.objects.get(session=session, year=year-1)
            if previous_turn.user_choice:
                # Get scenario_query_text from previous choice for RAG context
                query_text = previous_turn.user_choice.scenario_query_text
                logger.debug(f"Retrieved query text: {query_text[:50]}...")
                
                # Call RAG to get context_block
                if query_text.strip():
                    rag_chunks = retrieve_chunks(query_text)
                    context_block = preprocess_rag_chunks(rag_chunks)
                    logger.debug(f"Generated context block length: {len(context_block)}")
            else:
                logger.warning(f"Previous turn {year-1} has no user choice")
        except Turn.DoesNotExist:
            logger.warning(f"Previous turn {year-1} not found for session {session_id}")
    else:
        # First turn - use default context
        logger.info("First turn detected, using default context")
        # Randomly select 3 keywords from DefaultQueryList
        all_keywords = list(DefaultQueryList.objects.values_list('keyword', flat=True))
        if len(all_keywords) >= 3:
            import random
            default_keywords = random.sample(all_keywords, 3)
            logger.debug(f"Selected random keywords: {default_keywords}")
        elif all_keywords:
            # If less than 3 keywords available, use all of them
            default_keywords = all_keywords
            logger.debug(f"Using all available keywords: {default_keywords}")
        else:
            # No keywords available
            default_keywords = []
            logger.warning("No default keywords found in DefaultQueryList")
        
        if default_keywords:
            default_query = " ".join(default_keywords)
            rag_chunks = retrieve_chunks(default_query)
            context_block = preprocess_rag_chunks(rag_chunks)
        else:
            context_block = ""
    
    # Step 3: Prepare or retrieve story state for efficient LLM processing
    logger.info("Preparing story state for LLM generation...")
    try:
        if year == 2035:
            # First turn: Create initial story state
            current_story_state = create_story_state(
                scenario_summary="Government announces new memory editing technology capabilities, raising questions about ethics, policy, and societal impact"
            )
            logger.info("Created initial story state for first turn")
        else:
            # Subsequent turns: Get previous story state and update it
            try:
                previous_turn = Turn.objects.get(session=session, year=year-1)
                current_story_state = previous_turn.story_state or {}
                
                # Update story state based on previous turn's scenario summary
                if previous_turn.user_choice and previous_turn.user_choice.scenario_summary:
                    scenario_summary = previous_turn.user_choice.scenario_summary
                    logger.debug(f"Using previous choice scenario summary: {scenario_summary[:50]}...")
                else:
                    # Fallback if no scenario_summary available
                    scenario_summary = f"Story continues from year {year-1} with ongoing developments in memory editing technology and policy"
                    logger.debug("Using fallback scenario summary")
                
                current_story_state = update_story_state(
                    current_state=current_story_state,
                    new_scenario_summary=scenario_summary
                )
                logger.info(f"Updated story state for year {year} with scenario summary from previous choice")
                    
            except Turn.DoesNotExist:
                logger.warning(f"Previous turn {year-1} not found, creating fresh story state")
                current_story_state = create_story_state(
                    scenario_summary=f"Continuing from year {year-1} developments in memory editing technology and policy"
                )
    except Exception as e:
        logger.error(f"Story state preparation failed: {e}")
        # Fallback to empty state
        current_story_state = None

    # Step 4: Call LLM generation with story state
    logger.info("Calling LLM question generation...")
    try:
        question_result_json = generate_question(
            year=year,
            background=background,
            context_block=context_block,
            story_state=current_story_state
        )
        
        # Step 5: Parse the JSON result
        question_result = json.loads(question_result_json)
        logger.debug(f"LLM generated question: {question_result.get('question', '')[:50]}...")
        
    except Exception as e:
        logger.error(f"LLM question generation failed: {e}")
        raise
    
    # Step 6: Create new Turn record with story state
    try:
        new_turn = Turn.objects.create(
            session=session,
            year=year,
            question=question_result.get('question', ''),
            question_generated_at=timezone.now(),
            story_state=current_story_state or {}
        )
        logger.info(f"Created new turn {new_turn.id} for year {year}")
        
    except Exception as e:
        logger.error(f"Failed to create Turn record: {e}")
        raise
    
    # Step 7: Create two Option records
    options_data = question_result.get('options', [])
    option_queries = question_result.get('option_queries', [])
    
    if len(options_data) != 2 or len(option_queries) != 2:
        logger.error(f"Invalid options data: {len(options_data)} options, {len(option_queries)} queries")
        raise ValueError("LLM must generate exactly 2 options and 2 queries")
    
    created_options = []
    labels = ['A', 'B']
    
    try:
        for i, (label, option_text, query_text) in enumerate(zip(labels, options_data, option_queries)):
            option = Option.objects.create(
                turn=new_turn,
                label=label,
                option_text=option_text,
                scenario_query_text=query_text,
                created_at=timezone.now()
            )
            created_options.append(option)
            logger.debug(f"Created option {label}: {option_text[:30]}...")
        
        logger.info(f"Successfully created {len(created_options)} options for turn {new_turn.id}")
        
    except Exception as e:
        logger.error(f"Failed to create Option records: {e}")
        raise
    
    # Step 8: Return result summary
    result = {
        'turn_id': new_turn.id,
        'session_id': session_id,
        'year': year,
        'question': question_result.get('question', ''),
        'options': [
            {
                'id': opt.id,
                'label': opt.label,
                'text': opt.option_text,
                'query': opt.scenario_query_text
            }
            for opt in created_options
        ],
        'generated_at': new_turn.question_generated_at.isoformat()
    }
    
    logger.info(f"Question generation completed successfully for session {session_id}, year {year}")
    return result

@transaction.atomic
def generate_and_save_scenario(session_id: int, turn_id: int, year: int) -> Dict[str, Any]:
    """
    Generate scenario descriptions for the current turn's options and save to database.

    This function generates story outcomes for both options of a turn:
    1. Gather parameters from database (turn, options, previous context)
    2. Call LLM generation for scenario descriptions
    3. Save scenario and question_query_text results to Option records
    
    Args:
        session_id: The game session ID
        turn_id: The current turn ID (from generate_and_save_question)
        year: The current year for scenario generation
        
    Returns:
        Dict containing the generated scenario data
        
    Raises:
        Session.DoesNotExist: If session not found
        Turn.DoesNotExist: If turn not found
        Exception: If generation or database operations fail
    """
    logger.info(f"Starting scenario generation for session {session_id}, turn {turn_id}, year {year}")
    
    # Step 1: Get session and world background
    try:
        session = Session.objects.get(id=session_id)
        logger.debug(f"Retrieved session {session_id}")
    except Session.DoesNotExist:
        logger.error(f"Session {session_id} not found")
        raise
    
    try:
        world_background = WorldBackground.objects.first()
        background = world_background.content if world_background else ""
        logger.debug(f"Retrieved world background with length: {len(background)}")
    except Exception as e:
        logger.warning(f"Failed to retrieve world background: {e}")
        background = ""
    
    # Step 2: Get current turn and its question (using turn_id directly)
    try:
        current_turn = Turn.objects.get(id=turn_id, session=session)
        current_question = current_turn.question
        logger.debug(f"Retrieved current turn {current_turn.id} for session {session_id}")
        
        # Verify year consistency
        if current_turn.year != year:
            logger.warning(f"Year mismatch: turn has year {current_turn.year}, provided year {year}")
            
    except Turn.DoesNotExist:
        logger.error(f"Turn {turn_id} not found for session {session_id}")
        raise
    
    # Step 3: Get current turn's options
    options = Option.objects.filter(turn=current_turn).order_by('label')
    if options.count() != 2:
        logger.error(f"Expected 2 options for turn {current_turn.id}, found {options.count()}")
        raise ValueError(f"Turn must have exactly 2 options, found {options.count()}")
    
    option_texts = [opt.option_text for opt in options]
    scenario_queries = [opt.scenario_query_text for opt in options]
    
    logger.debug(f"Retrieved {len(option_texts)} options with scenario queries")
    
    # Step 4: Get context_blocks from scenario_query_text (one for each option)
    context_blocks = []
    
    for i, query_text in enumerate(scenario_queries):
        if query_text and query_text.strip():
            try:
                rag_chunks = retrieve_chunks(query_text)
                context_block = preprocess_rag_chunks(rag_chunks)
                context_blocks.append(context_block)
                logger.debug(f"Generated context block {i+1} length: {len(context_block)}")
            except Exception as e:
                logger.warning(f"Failed to retrieve RAG context for option {i+1}: {e}")
                context_blocks.append("")  # Empty fallback
        else:
            context_blocks.append("")  # Empty for missing query
            logger.warning(f"Empty scenario_query_text for option {i+1}")
    
    # Ensure we have exactly 2 context blocks
    if len(context_blocks) != 2:
        logger.warning(f"Expected 2 context blocks, got {len(context_blocks)}. Using empty fallbacks.")
        context_blocks = ["", ""]
    
        # Step 5: Get story state from current turn for scenario generation
    current_story_state = None
    if year > 2035:
        try:
            # Get story state from current turn (same as question generation)
            current_story_state = current_turn.story_state or {}
            logger.debug(f"Retrieved story state with {len(current_story_state.get('history', []))} history entries")
        except Exception as e:
            logger.warning(f"Failed to retrieve story state: {e}")
    else:
        logger.info("First turn (2035) detected, using no story state")

    # Step 6: Call LLM generation for option descriptions
    logger.info("Calling LLM scenario generation...")
    try:
        from llm.generate import generate_option_descriptions
        
        descriptions_result_json = generate_option_descriptions(
            year=year + 1,  # Next year for scenario projection
            background=background,
            context_blocks=context_blocks,  # Pass list of 2 context blocks
            current_question=current_question,
            options=option_texts,
            story_state=current_story_state
        )
        
        # Step 7: Parse the JSON result
        descriptions_result = json.loads(descriptions_result_json)
        logger.debug(f"LLM generated descriptions for {len(descriptions_result)} options")
        
    except Exception as e:
        logger.error(f"LLM scenario generation failed: {e}")
        raise
    
    # Step 8: Update Option records with generated scenarios and query texts
    updated_options = []
    
    try:
        for option in options:
            label = option.label
            if label in descriptions_result:
                description_data = descriptions_result[label]
                
                # Update scenario, scenario_summary and question_query_text fields
                option.scenario = description_data.get('scenario', '')
                option.scenario_summary = description_data.get('scenario_summary', '')
                option.question_query_text = description_data.get('query_text', '')
                option.save()
                
                updated_options.append(option)
                logger.debug(f"Updated option {label} with scenario length: {len(option.scenario)}")
            else:
                logger.warning(f"No description found for option {label}")
        
        logger.info(f"Successfully updated {len(updated_options)} options with scenarios")
        
    except Exception as e:
        logger.error(f"Failed to update Option records: {e}")
        raise
    
    # Step 9: Return result summary
    result = {
        'turn_id': current_turn.id,
        'session_id': session_id,
        'year': year,
        'question': current_question,
        'scenarios': [
            {
                'option_id': opt.id,
                'label': opt.label,
                'scenario': opt.scenario[:100] + '...' if len(opt.scenario) > 100 else opt.scenario,
                'query_text': opt.question_query_text
            }
            for opt in updated_options
        ],
        'generated_at': timezone.now().isoformat()
    }
    
    logger.info(f"Scenario generation completed successfully for session {session_id}, year {year}")
    return result

@transaction.atomic
def generate_and_save_image_text(session_id: int, turn_id: int, year: int) -> Dict[str, Any]:
    """
    Generate image description texts for the current turn's options and save to database.

    This function generates image descriptions for both options of a turn:
    1. Gather parameters from database (turn, options, previous context)
    2. Call LLM generation for image descriptions
    3. Save image_text results to Option records
    
    Args:
        session_id: The game session ID
        turn_id: The current turn ID (from generate_and_save_question)
        year: The current year for image text generation
        
    Returns:
        Dict containing the generated image text data
        
    Raises:
        Session.DoesNotExist: If session not found
        Turn.DoesNotExist: If turn not found
        Exception: If generation or database operations fail
    """
    logger.info(f"Starting image text generation for session {session_id}, turn {turn_id}, year {year}")
    
    # Step 1: Get session and world background
    try:
        session = Session.objects.get(id=session_id)
        logger.debug(f"Retrieved session {session_id}")
    except Session.DoesNotExist:
        logger.error(f"Session {session_id} not found")
        raise
    
    try:
        world_background = WorldBackground.objects.first()
        background = world_background.content if world_background else ""
        logger.debug(f"Retrieved world background with length: {len(background)}")
    except Exception as e:
        logger.warning(f"Failed to retrieve world background: {e}")
        background = ""
    
    # Step 2: Get current turn and its question (using turn_id directly)
    try:
        current_turn = Turn.objects.get(id=turn_id, session=session)
        current_question = current_turn.question
        logger.debug(f"Retrieved current turn {current_turn.id} for session {session_id}")
        
        # Verify year consistency
        if current_turn.year != year:
            logger.warning(f"Year mismatch: turn has year {current_turn.year}, provided year {year}")
            
    except Turn.DoesNotExist:
        logger.error(f"Turn {turn_id} not found for session {session_id}")
        raise
    
    # Step 3: Get current turn's options
    options = Option.objects.filter(turn=current_turn).order_by('label')
    if options.count() != 2:
        logger.error(f"Expected 2 options for turn {current_turn.id}, found {options.count()}")
        raise ValueError(f"Turn must have exactly 2 options, found {options.count()}")
    
    option_texts = [opt.option_text for opt in options]
    logger.debug(f"Retrieved {len(option_texts)} options for image generation")
    
    # Step 4: Get last_description from previous turn
    last_description = ""
    if year > 2035:
        try:
            previous_turn = Turn.objects.get(session=session, year=year-1)
            if previous_turn.user_choice and previous_turn.user_choice.scenario:
                last_description = previous_turn.user_choice.scenario
                logger.debug(f"Retrieved last description length: {len(last_description)}")
            else:
                logger.warning(f"Previous turn {year-1} has no user choice or scenario")
        except Turn.DoesNotExist:
            logger.warning(f"Previous turn {year-1} not found for session {session_id}")
    else:
        logger.info("First turn (2035) detected, using empty last_description")
    
    # Step 5: Call LLM generation for image descriptions
    logger.info("Calling LLM image text generation...")
    try:
        from llm.generate import generate_option_image_texts
        
        image_text_result_json = generate_option_image_texts(
            year=year,
            background=background,
            last_description=last_description,
            question=current_question,
            options=option_texts
        )
        
        # Step 6: Parse the JSON result
        image_text_result = json.loads(image_text_result_json)
        logger.debug(f"LLM generated image texts for {len(image_text_result)} options")
        
    except Exception as e:
        logger.error(f"LLM image text generation failed: {e}")
        raise
    
    # Step 7: Update Option records with generated image texts
    updated_options = []
    
    try:
        for option in options:
            label = option.label
            if label in image_text_result:
                image_text = image_text_result[label]
                
                # Update image_text field
                option.image_text = image_text
                option.save()
                
                updated_options.append(option)
                logger.debug(f"Updated option {label} with image text length: {len(image_text)}")
            else:
                logger.warning(f"No image text found for option {label}")
        
        logger.info(f"Successfully updated {len(updated_options)} options with image texts")
        
    except Exception as e:
        logger.error(f"Failed to update Option records: {e}")
        raise
    
    # Step 8: Return result summary
    result = {
        'turn_id': current_turn.id,
        'session_id': session_id,
        'year': year,
        'question': current_question,
        'image_texts': [
            {
                'option_id': opt.id,
                'label': opt.label,
                'image_text': opt.image_text[:100] + '...' if len(opt.image_text) > 100 else opt.image_text
            }
            for opt in updated_options
        ],
        'generated_at': timezone.now().isoformat()
    }
    
    logger.info(f"Image text generation completed successfully for session {session_id}, year {year}")
    return result

def get_session_status(session_id: int) -> Dict[str, Any]:
    """
    Get the current status and progress of a game session.
    
    Args:
        session_id: The game session ID
        
    Returns:
        Dict containing session status information
    """
    try:
        session = Session.objects.get(id=session_id)
        turns = Turn.objects.filter(session=session).order_by('year')
        
        current_year = turns.last().year if turns.exists() else 2034
        completed_turns = turns.filter(user_choice__isnull=False).count()
        
        return {
            'session_id': session_id,
            'current_year': current_year,
            'next_year': current_year + 1,
            'completed_turns': completed_turns,
            'total_turns': turns.count(),
            'has_pending_choice': turns.filter(user_choice__isnull=True).exists()
        }
        
    except Session.DoesNotExist:
        return {'error': f'Session {session_id} not found'}

def record_user_choice(turn_id: int, option_id: int) -> Dict[str, Any]:
    """
    Record a user's choice for a specific turn.
    
    Args:
        turn_id: The turn ID
        option_id: The chosen option ID
        
    Returns:
        Dict containing the updated turn information
    """
    try:
        with transaction.atomic():
            turn = Turn.objects.get(id=turn_id)
            option = Option.objects.get(id=option_id, turn=turn)
            
            turn.user_choice = option
            turn.save()
            
            logger.info(f"Recorded user choice: Turn {turn_id}, Option {option.label}")
            
            return {
                'turn_id': turn_id,
                'chosen_option': {
                    'id': option.id,
                    'label': option.label,
                    'text': option.option_text
                },
                'success': True
            }
            
    except (Turn.DoesNotExist, Option.DoesNotExist) as e:
        logger.error(f"Failed to record user choice: {e}")
        return {'error': str(e), 'success': False}

from images.display import display_by_option
def display_world_view(session_id: int, turn_id: int, year: int, option_id: int) -> Dict[str, Any]:
    """
    Display the world view after user makes a choice.
    
    Returns both the scenario text and image info for the selected option.
    This is called after user clicks on an option to show the consequences.
    
    Args:
        session_id: The game session ID
        turn_id: The current turn ID 
        year: The current year (for validation)
        option_id: The option the user selected
        
    Returns:
        Dict containing scenario text and image info as JSON
    """
    
    # Step 1: Get the scenario text from the selected option
    try:
        turn = Turn.objects.get(id=turn_id, session=session_id)
        option = Option.objects.get(id=option_id, turn=turn)
        
        # Get the scenario text that was generated for this option
        scenario_to_display = option.scenario or ""
        
        logger.info(f"Retrieved scenario for option {option.label}: {len(scenario_to_display)} characters")
        
    except (Turn.DoesNotExist, Option.DoesNotExist) as e:
        logger.error(f"Failed to get scenario: {e}")
        return {
            "error": f"Turn or Option not found: {e}",
            "success": False
        }
    
    # Step 2: Get the image info
    try:
        image_info = display_by_option(session_id, turn_id, option_id)
        logger.info(f"Retrieved image info: {image_info.get('status', 'unknown')}")
        
    except Exception as e:
        logger.error(f"Failed to get image info: {e}")
        return {
            "error": f"Failed to get image info: {e}",
            "success": False
        }
    
    # Step 3: Combine everything into a JSON response
    world_view_response = {
        "success": True,
        "session_id": session_id,
        "turn_id": turn_id,
        "year": year,
        "scenario": {
            "text": scenario_to_display,
        },
        "image": {
            "status": image_info.get("status", "unknown"),
            "url": image_info.get("image_url", ""),
        },
    }
    
    logger.info(f"World view display completed for session {session_id}, turn {turn_id}, option {option.label}")
    
    return world_view_response


# # this is refactored by start_turn_pipeline in tasks.py
# @transaction.atomic
# def generate_complete_turn(session_id: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
#     """
#     Generate a complete turn including question, image texts, and scenarios.
    
#     This function orchestrates the complete turn generation workflow:
#     1. Check or create session
#     2. Determine the appropriate year
#     3. Generate question and options
#     4. Generate image texts for options
#     5. Generate scenarios for options
    
#     Args:
#         session_id: Optional existing session ID. If None, creates new session
#         year: Optional target year. If None, determines next available year
        
#     Returns:
#         Dict containing all generated data and metadata
        
#     Raises:
#         ValueError: If year exceeds 2085 limit
#         Exception: If any generation step fails
#     """
#     logger.info(f"Starting complete turn generation for session {session_id}, year {year}")
    
#     start_time = timezone.now()
    
#     # Step 1: Handle session creation/validation
#     # Brynn: I do not think session should be created here, it should be at the home page view
#     # is there any year limit?
#     try:
#         if session_id is None:
#             # Create new session
#             session = Session.objects.create(created_at=timezone.now())
#             session_id = session.id
#             target_year = 2035  # Start from first year
#             logger.info(f"Created new session {session_id}")
#         else:
#             # Validate existing session
#             try:
#                 session = Session.objects.get(id=session_id)
#                 logger.debug(f"Retrieved existing session {session_id}")
                
#                 # Determine next year if not provided
#                 if year is None:
#                     latest_turn = Turn.objects.filter(session=session).order_by('-year').first()
#                     target_year = latest_turn.year + 1 if latest_turn else 2035
#                 else:
#                     target_year = year
                    
#             except Session.DoesNotExist:
#                 logger.warning(f"Session {session_id} not found, creating new session")
#                 session = Session.objects.create(created_at=timezone.now())
#                 session_id = session.id
#                 target_year = year if year is not None else 2035
        
#         # Step 2: Validate year limit
#         if target_year > 2085:
#             logger.error(f"Year {target_year} exceeds maximum limit of 2085")
#             # Create new session for a fresh start
#             session = Session.objects.create(created_at=timezone.now())
#             session_id = session.id
#             target_year = 2035
#             logger.info(f"Created new session {session_id} due to year limit, starting from 2035")
        
#         logger.info(f"Target generation: Session {session_id}, Year {target_year}")
        
#     except Exception as e:
#         logger.error(f"Failed to handle session setup: {e}")
#         raise
    
#     # Step 3: Generate question and options
#     step_start = timezone.now()
#     try:
#         logger.info("Step 1/3: Generating question and options...")
#         question_result = generate_and_save_question(session_id, target_year)
#         turn_id = question_result['turn_id']
#         step_duration = (timezone.now() - step_start).total_seconds()
#         logger.info(f"Question generation completed in {step_duration:.2f}s, Turn ID: {turn_id}")
        
#     except Exception as e:
#         logger.error(f"Question generation failed: {e}")
#         raise
    
#     # Step 4: Generate image texts
#     step_start = timezone.now()
#     try:
#         logger.info("Step 2/3: Generating image texts...")
#         image_result = generate_and_save_image_text(session_id, turn_id, target_year)
#         step_duration = (timezone.now() - step_start).total_seconds()
#         logger.info(f"Image text generation completed in {step_duration:.2f}s")
#         # TODO: Reserved space for image generation function
#         generate_two_images_blocking(session_id, turn_id)
        
#     except Exception as e:
#         logger.error(f"Image text generation failed: {e}")
#         raise
    
#     # Step 5: Generate scenarios
#     step_start = timezone.now()
#     try:
#         logger.info("Step 3/3: Generating scenarios...")
#         scenario_result = generate_and_save_scenario(session_id, turn_id, target_year)
#         step_duration = (timezone.now() - step_start).total_seconds()
#         logger.info(f"Scenario generation completed in {step_duration:.2f}s")
        
#     except Exception as e:
#         logger.error(f"Scenario generation failed: {e}")
#         raise
    
#     # Step 6: Compile complete result
#     total_duration = (timezone.now() - start_time).total_seconds()
    
#     result = {
#         'session_id': session_id,
#         'turn_id': turn_id,
#         'year': target_year,
#         'created_new_session': session_id != session_id if session_id else True,  # Simplified logic
#         'total_duration': total_duration,
#         'generation_steps': {
#             'question': {
#                 'success': True,
#                 'turn_id': question_result['turn_id'],
#                 'question': question_result['question'],
#                 'options': question_result['options'],
#                 'generated_at': question_result['generated_at']
#             },
#             'image_texts': {
#                 'success': True,
#                 'image_texts': image_result['image_texts'],
#                 'generated_at': image_result['generated_at']
#             },
#             'images': {
#                 'success': True,
#             },
#             'scenarios': {
#                 'success': True,
#                 'scenarios': scenario_result['scenarios'],
#                 'generated_at': scenario_result['generated_at']
#             }
#         },
#         'completed_at': timezone.now().isoformat()
#     }
    
#     logger.info(f"Complete turn generation finished successfully")
#     logger.info(f"Session: {session_id}, Turn: {turn_id}, Year: {target_year}")
#     logger.info(f"Total duration: {total_duration:.2f}s")
    
#     return result
