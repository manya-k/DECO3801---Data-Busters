from typing import List

def build_question_prompt(
    year: int,
    background: str,
    context_block: str,
    last_description: str,
) -> str:
    """
    STEP A: Ask the model to return a RAG query AND a multiple-choice style question with two options.
    OUTPUT must be STRICT JSON with fields: query_text, question, options[2]
    """
    return f"""
You are a narrative engine for a turn-based story.

TASK
1) Build a retrieval query to fetch 3–6 highly relevant factual snippets for grounding.
2) Propose ONE clear, decision-driving question WITH EXACTLY TWO OPTIONS (A, B). 
   Each option must be short, mutually exclusive, and lead to meaningfully different outcomes.

STORY FRAME
Current Year: {year}

Background:
{background}

Previous Story Summary:
{last_description}

Retrieved Context (if any, distilled):
{context_block}


HARD CONSTRAINTS
- Return ONLY valid JSON (no markdown, no code fences).
- The question must be specific and consequential for the next plot turn.
- "options": an array of EXACTLY 2 strings. Avoid "Yes/No".
- The retrieval query must be standalone (<= 110 chars) and safe to send to RAG.
- Each option must be short (6–14 words), mutually exclusive, concrete, and must NOT repeat the question text.
- Do NOT include labels like "A." or "B." inside option strings.
- The two options MUST represent distinctly different approaches or philosophies.
- Options should be self-contained and understandable without repeating the whole question.
- Frame the question at the societal, policy, or community level (e.g., citizens, regulators, clinics, researchers).

OUTPUT FORMAT (STRICT)
Return ONLY valid JSON with this exact schema:
{{
  "query_text": "<<=110 chars, standalone retrieval sentence>",
  "question": "<one question ending with a question mark>",
  "options": ["<option A>", "<option B>"]
}}

EXAMPLE (ONLY to learn the shape; DO NOT copy content):
{{
  "query_text": "clinical protocols for identity continuity in memory-editing pilots",
  "question": "Which approach should the regulatory committee prioritize?",
  "options": ["Establish mandatory waiting periods for all procedures", "Create independent patient advocate programs"]
}}

Return ONLY valid JSON. Do not include markdown, code fences, or commentary.
""".strip()


def build_description_prompt(
    year: int,
    background: str,
    context_block: str,
    last_description: str,
    current_question: str,
    selected_option: str,   # one of the strings from the options array
) -> str:
    """
    STEP B: Given the player's selected option, produce the Scenario + follow-up RAG query.
    OUTPUT must be STRICT JSON:
    - scenario: single paragraph string which is vivid and engaging.
    - query_text: declarative keyword phrase (no questions) for the NEXT turn's retrieval.
    """
    return f"""
You are continuing a turn-based story. Incorporate the selected option and produce:
1) A concrete scenario paragraph which is vivid and engaging.
2) A focused follow-up retrieval query as a declarative keyword phrase (not a question).

CRITICAL VALIDATION REQUIREMENTS (Your response will be automatically validated):
1. MUST return valid JSON format (no extra text before/after)
2. MUST include "scenario" field as a string paragraph
3. MUST include "query_text" field as a string
4. Total word count for the scenario paragraph must be between 80-150 words
5. If any of these requirements are not met, your response will be rejected and retried

STORY FRAME
Current Year: {year}

Background:
{background}

Previous Story Summary:
{last_description}

Retrieved Context (if any, distilled):
{context_block}

Current Question:
{current_question}

Selected Option:
{selected_option}

SCENARIO REQUIREMENTS
- Output "scenario" as a single coherent paragraph string.
- CRITICAL: Total word count MUST be between 80-150 words (count words by spaces). Your response will be REJECTED if under 80 words.
- Write as one flowing narrative paragraph with multiple detailed sentences (aim for 4-6 sentences minimum).
- Focus on institutional actors (clinics, agencies, councils, governments, consortia). Do not center individual doctors or patients; avoid personal names.
- Overall causal arc: an institutional actor takes an action → visible consequences or public reactions. You do not need to repeat this structure inside every sentence.
- Use simple, everyday language suitable for museum visitors or high-school students.
- Make it vivid and engaging: include sensory details (lights, sounds, crowds) and small dramatic contrasts; at least one sentence should invite reflection with a question.
- Add specific details: mention concrete locations, times, numbers, reactions, and outcomes to reach the required length.
- Do not use arrows, symbols, headings, or labels like "result:"; write only natural sentences.

ANTI-COPYING & VARIATION
- Do not copy wording from any example. Use different phrasing and fresh details.
- Avoid these phrases entirely: "brightly lit", "holograms", "bustling public square", "marble walls", "glowing buttons".
- Use different cities/venues than any example; vary institutions and settings.

EXAMPLE TEMPLATE (structure only, NOT content to copy - this example is approximately 95 words):
"scenario": "<Government/Agency/Clinic/Consortium> announces a comprehensive policy/action at <specific venue and city> on <specific date>, explaining detailed goals and multiple safeguards while diverse audiences react with curiosity and measured caution about identity preservation and privacy implications. <Regulatory body/Clinic network> demonstrates standardized procedures under strict multi-step consent checks, describing verification protocols and displaying preliminary results as visitors carefully weigh potential cognitive benefits against possible psychological risks and societal consequences. <Council/Agency> hosts an extensive public session in <concrete setting and time>, where detailed signage, ambient sounds, and interactive screen visuals shape the contemplative mood and make complex scientific ideas feel tangible and accessible. <Government/Consortium> coordinates systematically with regional partners, promising rigorous oversight and transparent reporting, while ongoing debates and news coverage amplify both hopes alongside growing doubts about long-term consequences. What fundamental aspects of human identity should be protected if memories become editable in daily life?"

CRITICAL LENGTH REQUIREMENT
- YOUR RESPONSE WILL BE AUTOMATICALLY REJECTED IF THE SCENARIO IS UNDER 80 WORDS.
- Target 100-120 words for optimal length (well within the 80-150 range).
- Include multiple detailed sentences with specific examples, locations, reactions, and consequences.
- Add descriptive elements: specific venues, participant reactions, timeline details, policy specifics.
- Count words carefully before finalizing your response.
- Never include banned phrases.

FOLLOW-UP RAG QUERY REQUIREMENTS
- Base the query strictly on entities, mechanisms, or ethical dilemmas explicitly raised in the scenario.
- Do not introduce unrelated topics.
- CRITICAL: Write as a DECLARATIVE STATEMENT, not a question.
- Format: "topic keywords and concepts" or "subject matter and related terms"
- Examples: "memory editing consent procedures and safety protocols" | "clinical trial regulations and patient rights" | "institutional oversight and ethical guidelines"
- Do NOT use question words (what, how, why, should, can, will, etc.) or question marks (?)

OUTPUT FORMAT (STRICT)
CRITICAL: Your response will be validated automatically. It MUST pass these checks:
1. Valid JSON format (starts with {{ and ends with }})
2. Contains "scenario" field as a string paragraph
3. MANDATORY: Total word count of the scenario paragraph must be between 80-150 words (WILL BE REJECTED IF UNDER 80)
4. Contains "query_text" field as a string
5. No extra text outside the JSON structure

BEFORE SUBMITTING: Count the words in your scenario. If under 80 words, add more specific details, institutional reactions, timeline information, or consequences until you reach at least 80 words.

Return ONLY valid JSON with this exact schema:
{{
  "scenario": "<one coherent paragraph with 80-150 words total>",
  "query_text": "<declarative keyword phrase - no questions or question marks>"
}}

REMINDER: If the total word count is not between 80-150 words, your response will be rejected.
Return ONLY valid JSON. Do not include markdown, code fences, or commentary.
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
