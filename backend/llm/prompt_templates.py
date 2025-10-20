from typing import List

STORY_LANGUAGE_RULES = """
Write like you're telling a story to everyone, including kids aged 10-14:
- Use simple words: "groups" not "institutions", "people" not "participants", "rules" not "regulations"
- Use action words: "create" not "establish", "start" not "implement", "watch" not "monitor", "decide" not "determine"
- Avoid academic terms like "ethical", "clinical", "framework", "mandate", "utilize"
- Sound curious and friendly, not formal or academic
- Keep each sentence very short (maximum 15 words each) - NO long, complex sentences
- Never combine multiple ideas in one sentence - break them into separate short sentences
- Make it feel like part of an ongoing story
- Use concrete things everyone can imagine: new laws, habits, public reactions
"""

def build_question_prompt(
    year: int,
    background: str,
    context_block: str,
) -> str:
    """
    Generate a prompt for LLM to create a progressive, time-aware 2-option question
    with per-option RAG queries. Includes anti-repetition and theme progression.
    
    Returns:
        A single JSON object (no markdown).
    """
    # Map year to developmental phase and thematic focus (every 10 years with logical progression)
    if year < 2040:
        phase = "testing-and-safety"
        phase_themes = "early tests, safety rules, doctor training, first clinics, basic privacy laws"
    elif year < 2050:
        phase = "public-access"
        phase_themes = "public hospitals offer it, cost problems, insurance fights, rich vs poor access, first regulations"
    elif year < 2060:
        phase = "work-and-school"
        phase_themes = "job changes, school programs, memory help for learning, workplace rules, family decisions"
    elif year < 2070:
        phase = "government-control"
        phase_themes = "government watching, memory evidence in courts, citizen records, voting concerns, protest rights"
    elif year < 2080:
        phase = "world-conflicts"
        phase_themes = "country fights over memory tech, trade wars, memory spying, cultural protection, border controls"
    else:
        phase = "new-society"
        phase_themes = "kids grow up with it, changed human nature, memory trading, identity questions, what makes us human"

    # Check if context_block contains compressed context from story state
    if "Story History:" in context_block:
        world_ctx = f"""CURRENT WORLD STATE
Year: {year}
Phase: {phase}
Phase-Themes: {phase_themes}

Story History (HIGH PRIORITY):
{context_block}

Initial Setting (reference only): {background}
"""
    else:
        world_ctx = f"""CURRENT WORLD STATE
Year: {year}
Phase: {phase}
Phase-Themes: {phase_themes}

Setting (first turn or RAG-only):
{background}

Available Context:
{context_block}
"""
    
    return f"""<|system|>
You are a storyteller for a turn-based museum game about future memory technology. Sound curious and imaginative, not academic.

LANGUAGE: {STORY_LANGUAGE_RULES}

MISSION: Create JSON with question that ends with question mark, options "[WHICH GROUP] should [ACTION] so that [RESULT]", option_queries (3-6 keywords each).

QUESTION FORMAT:
1. Story sentence about this year (end with .)
2. Question about what groups should do next (end with ?)
3. Combine both under 35 words total
- MUST end with "?" 
- Ask about big groups (cities/hospitals/schools), not individuals
- Show how world changed and what problem groups face

OPTIONS FORMAT:
- Two opposite approaches to SAME problem
- Structure: "[WHICH GROUP] should [ACTION] so that [RESULT]"
- MUST use group names like: cities, hospitals, schools, governments, companies, communities, families
- No symbols like [ or " in final output
- No keywords in options
- Both must directly answer the question

KEYWORD EXTRACTION:
- Extract 3-6 key nouns/phrases from each option
- Example: "memory editing consent procedures"

OUTPUT: Valid JSON only with: question, options, option_queries
Use normal English, no random numbers/broken text.
<|end|>
<|user|>
WORLD STATE: {world_ctx}
Phase: {phase} ({phase_themes})
Year: {year}

Create a story question about what happened and what groups should do next, with two opposite options and two keyword queries.
<|end|>
<|assistant|>""".strip()


def build_description_prompt(
    year: int,
    background: str,
    context_block: str,
    current_question: str,
    selected_option: str,
) -> str:
    """
    Generate a prompt for LLM to create a progressive, time-aware scenario description
    based on the selected option. Includes world state evolution and narrative continuity.
    
    Returns:
        A single JSON object with scenario, scenario_summary, and query_text fields.
    """
    
    # Map year to developmental phase and thematic focus (every 10 years with logical progression)
    if year < 2040:
        phase = "testing-and-safety"
        phase_themes = "early tests, safety rules, doctor training, first clinics, basic privacy laws"
    elif year < 2050:
        phase = "public-access"
        phase_themes = "public hospitals offer it, cost problems, insurance fights, rich vs poor access, first regulations"
    elif year < 2060:
        phase = "work-and-school"
        phase_themes = "job changes, school programs, memory help for learning, workplace rules, family decisions"
    elif year < 2070:
        phase = "government-control"
        phase_themes = "government watching, memory evidence in courts, citizen records, voting concerns, protest rights"
    elif year < 2080:
        phase = "world-conflicts"
        phase_themes = "country fights over memory tech, trade wars, memory spying, cultural protection, border controls"
    else:
        phase = "new-society"
        phase_themes = "kids grow up with it, changed human nature, memory trading, identity questions, what makes us human"

    # Build world context with conditional handling
    if "Story History:" in context_block:
        world_ctx = f"""CURRENT WORLD STATE
Year: {year}
Phase: {phase}
Phase-Themes: {phase_themes}

Story History (HIGH PRIORITY):
{context_block}

Current Question: {current_question}

Selected Option: {selected_option}

Initial Setting (reference only): {background}
"""
    else:
        world_ctx = f"""CURRENT WORLD STATE
Year: {year}
Phase: {phase}
Phase-Themes: {phase_themes}

Setting (first turn or RAG-only):
{background}

Available Context:
{context_block}

Current Question: {current_question}

Selected Option: {selected_option}
"""
    
    return f"""
ROLE
You are a storyteller continuing the future memory technology story.
Your job is to show what happens next after players make their choice, telling it like an exciting story chapter.
Focus on what people can see, hear, and feel in this changed world.

LANGUAGE GUIDE
{STORY_LANGUAGE_RULES}

CORE MISSION
Generate a descriptive scenario (80-150 words) showing what happens after the selected option "{selected_option}" is implemented in {year}. 
Write a narrative description of concrete consequences and changes - not instructions or questions. Include specific details about institutions, policies, and public reactions to meet length requirements.

WORLD STATE & DECISION CONTEXT (read carefully; highest priority)
{world_ctx}

NARRATIVE PROGRESSION REQUIREMENTS
- WORLD CONTEXT PRIORITY: Use ALL information from {world_ctx} above - especially Story History - as foundation for new developments
- STORY CONTINUITY: Build upon Story Context/History but create NEW developments that show how the selected option "{selected_option}" uniquely changes the world
- ANTI-REPETITION: Avoid repeating situations, phrases, or outcomes from previous scenarios - introduce at least 2 completely new elements (institutions, policies, locations, conflicts)
- CHOICE SPECIFICITY: Show concrete, measurable results that directly stem from the selected option (new laws with specific names, public reactions in named locations, institutional changes with details)
- FORWARD PROGRESSION: Move beyond basic actions to explore fresh consequences and emerging challenges never seen before
- PRIORITY: Story Context/History takes precedence over background information - use it to create contrast and novelty

SCENARIO WRITING GUIDE
- CRITICAL YEAR REQUIREMENT: The FIRST sentence MUST start with {year} to establish temporal context, and the last sentence must end with a full stop (.)
- Include specific details about this time period: concrete dates, new institution names, people's reactions, policy details, and sensory atmosphere  
- Write as one flowing story paragraph with 5-7 detailed sentences, 80-130 words total (CRITICAL: MUST BE AT LEAST 80 words or response will be rejected)
- Focus on big groups (clinics, agencies, councils, governments, companies). Do not center individual doctors or patients; avoid personal names
- Structure: Selected option implementation → Specific results happen → Public reacts → New challenges emerge
- Make it vivid and interesting: include what you can see/hear/feel (lights, sounds, crowds) and small dramatic differences; at least one sentence should make people think with a question
- Balance simplicity with adequate detail - each sentence should contribute meaningful information

FOLLOW-UP RAG QUERY REQUIREMENTS
- Extract key entities and concepts from the scenario as a declarative keyword phrase
- Format: "topic keywords and concepts" (no questions or question marks)
- Examples: "memory editing consent procedures" | "clinical trial regulations" | "institutional oversight guidelines"

SCENARIO SUMMARY NEEDS
- Look at how the chosen option changes the world described in the Story Context
- Capture the key change: what moves from the old state to the new state
- Length: 20-30 words focusing on real group, social, or rule changes
- Example: "New international memory editing standards create citizen registry system, while underground modification networks emerge in response to restrictions"

TASK SPECIFICATION
1) Generate a concrete scenario paragraph which is vivid and engaging
2) Create a focused follow-up retrieval query as a declarative keyword phrase
3) Provide a scenario summary that captures world state changes

OUTPUT FORMAT
- Return ONLY valid JSON with: scenario, scenario_summary, query_text
- Scenario: MUST start with {year}, 80-130 words
- Summary: 20-30 words about world changes
- Query: keyword phrase (no questions)

Check your output: if too short or doesn't meet requirements, revise it.
""".strip()


def build_image_text_prompt(
    year: int,
    background: str,
    last_description: str,
    question: str,
    option_text: str,
) -> str:
    """
    Build a prompt to generate an image description for a specific option.
    This predicts what the visual scene would look like if this option is chosen.
    """
    return f"""
You are helping generate speculative art style image prompts for an AI image generation model.

The current world state is: {background}

Previous events: {last_description}

Current situation (Year {year}): {question}

If this option is chosen: {option_text}

Your task: Write one single detailed image prompt that captures the atmosphere of this world after choosing this specific option.

STRICT REQUIREMENTS:
- Output EXACTLY ONE sentence (no line breaks, no multiple sentences)
- Maximum 70 words (count your words carefully)
- Maximum 350 characters including spaces
- Use concrete, visual language only
- No quotes, no explanations, no meta-commentary
- No instruction acknowledgments (do not say "Here's" or "I'll create")

Focus on:
- The environment and overall scene (urban, rural, futuristic, dystopian, natural, etc.)
- The emotional mood (hopeful, doomed, neutral, chaotic, peaceful, tense, etc.) 
- The artistic style (speculative art, cinematic, surreal, painterly textures, neon lighting)

Do not describe exact numbers of people or micro actions. Instead, describe the overall crowd impression and the vibe of the world.

EXAMPLES (for structure reference only, create original content):
- "A cinematic government facility bathed in cold fluorescent lighting with officials reviewing documents at sterile desks"
- "Speculative art scene of a bustling clinic courtyard with hopeful citizens waiting under warm sunset lighting"

CRITICAL: Output only the final image prompt as one complete sentence. No additional text, explanations, or commentary.
""".strip()
