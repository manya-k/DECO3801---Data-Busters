from typing import List

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
    
    return f"""


ROLE
You are a storyteller for a turn-based museum game about the future of memory technology.
You speak in clear, friendly, story-like language that kids aged 10–14 can understand.
Each round, you ask a question about what groups like groups, cities, or governments etc. should do next.
Your words should sound curious and imaginative, not formal or academic.

CORE MISSION
Ask a story question that moves time forward and fits the current year {year}.
The question should show how the world has changed and what new problem people or groups face now, within the {phase_themes}.
Make it sound like part of a story, not like a report or plan.

WORLD STATE & CONTEXT (read carefully; highest priority)
{world_ctx}

STORY PROGRESSION PRINCIPLES
- PRIORITY: Keep the world story moving forward each year. Mention how life feels different now.
- REQUIRED: Focus on what people notice or experience because of past choices.
- ADVANCED: Show new problems or exciting changes that make the next decision important.
- BE SPECIFIC: Describe simple, concrete things that kids can imagine — like new laws, new habits, or public reactions.
- AVOID: Academic words like “institutions”, “regulations”, “participants”, “ethical”, or “clinical”.
  Use simple ones like “groups”, “rules”, “people”, “safe”, “fair”, or “new idea”.

QUESTION BUILDING GUIDE
STEP 1: Write one short story sentence about what is happening this year ({year}).
STEP 2: Ask a clear question (end with '?') about what people or groups should do next.
STEP 3: Write two opposite options (15–18 words each) following the OPTION BUILDING GUIDE below.
Keep both parts simple and under 25 words in total.
- Use clear, story-like language that everyone, including children, can easily understand, without directly addressing the reader.
- Write for institutions, governments, or large groups (not individuals)
- Make the question interesting and important
- Replace overly complex terms with simpler alternatives when possible: "establish"→"create", "implement"→"start", "institutions"→"groups", "participants"→"people", "consequences"→"results", utilize"→"use", "determine"→"decide", "eliminate"→"remove", "monitor"→"watch"

OPTION BUILDING GUIDE
- Use simple words everyone can understand, including children.
- Write 2 clear actions (15–18 words each) that stay directly relevant to the question.
- The choices should show different ways to solve the same problem: one strict/careful, the other open or exploratory.
- Avoid abstract or policy terms like "regulate", "mandate", or "framework".
- Both options must sound logical and reasonable within the story.

--- KEYWORD EXTRACTION TASK ---
- Extract 3–6 key nouns or short phrases from each option.
- Only use concrete words, no verbs or question words.
- Write them in one line, separated by spaces.
- Example: "memory editing safety rules"

OUTPUT REQUIREMENTS
- Use only normal English words, no random numbers or broken text
- Return ONLY valid JSON with these parts: question, options, option_queries

Example:
{{"question": "Memory editing clinics are getting crowded and many people are waiting. How should hospitals help more people get treatment?", "options": ["Open more clinics in different cities to serve everyone", "Make people wait longer but give better and safer care"], "option_queries": ["expanding medical facilities", "healthcare quality improvement"]}}

Check your own output: if one option sounds silly, off-topic, or humorous, rewrite it seriously.
""".strip()



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

    # Build world context with conditional handling (like build_question_prompt)
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
You are a narrative engine for a turn-based story about humanity's relationship with memory editing technology.

CORE MISSION
Produce a vivid, time-aware scenario description that incorporates the selected option and advances the story timeline appropriate for the '{phase}' phase. Focus primarily on themes relevant to this time period.

WORLD STATE & DECISION CONTEXT (read carefully; highest priority)
{world_ctx}

WORLD STATE GROWTH RULES
- The story moves forward through different stages of social change
- Story Connection: Each scenario must build upon what happened before and past decisions
- Theme Growth: Move beyond basic actions to explore what happens next and how people react
- PRIORITY: Story Context/History above is more important than background information

NARRATIVE PROGRESS NEEDS
- MANDATORY: Read the Story Context/History to understand what has already happened
- FORBIDDEN: Go back to earlier times or repeat solved problems
- REQUIRED: Focus on SPECIFIC results, reactions, or new things that happen from the chosen option
- ADVANCED: Each scenario should show how the world has changed and bring up new challenges
- BE SPECIFIC: Talk about real results (rule changes, public reactions, group changes, social fights)

SCENARIO WRITING GUIDE
- MANDATORY YEAR REFERENCE: Start your scenario by mentioning the current year ({year}) in the opening sentence to establish when this is happening
- Include specific details about this time period: real dates, places, group names, people's reactions, rule details, and what you can see/hear/feel  
- Write as one flowing story paragraph with 5-8 detailed sentences, 80-150 words total (CRITICAL: MUST BE AT LEAST 80 words or response will be rejected)
- Focus on big groups (clinics, agencies, councils, governments, companies). Do not center individual doctors or patients; avoid personal names
- Structure: Group takes action → Results happen → Public reacts → Thinking question (don't force this pattern into every sentence)
- Use clear, accessible language that children can understand but with sufficient detail for length requirements
- Make it vivid and interesting: include what you can see/hear/feel (lights, sounds, crowds) and small dramatic differences; at least one sentence should make people think with a question
- Balance simplicity with adequate detail - each sentence should contribute meaningful information

LANGUAGE CLARITY REQUIREMENTS FOR SCENARIOS
- Use clear, simple language appropriate for young readers while maintaining narrative richness
- Replace overly complex terms with simpler alternatives when possible: "establish"→"create", "implement"→"start", "institutions"→"groups", "participants"→"people", "consequences"→"results", utilize"→"use", "determine"→"decide", "eliminate"→"remove", "monitor"→"watch"
- CRITICAL LENGTH REQUIREMENT: Your response must contain at least 80 words to be accepted - add descriptive details about settings, reactions, and consequences
- Include rich descriptions of what happens, how people react, what institutions do, and what changes occur
- Each sentence should add substantial detail rather than just basic facts - describe scenes, emotions, and outcomes thoroughly

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

OUTPUT FORMAT (automatically validated):
- Valid JSON with exactly these fields: scenario, scenario_summary, query_text  
- Scenario: MUST start with the year {year}, then single coherent paragraph, 80-150 words (WILL BE REJECTED IF UNDER 80 words - aim for 85-120 words)
- Scenario summary: 20-30 words focusing on world state changes and story progression
- Query text: Declarative keyword phrase (no questions)
- FORBIDDEN: Template variables, brackets, HTML-like syntax, placeholder text
- No markdown, code fences, or extra commentary
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
