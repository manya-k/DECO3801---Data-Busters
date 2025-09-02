"""
API views for handling storyline-related requests.
Provides endpoints to fetch story background, questions, and results based on user choices.
"""
import json
import os
import logging
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .game_state import submit_choice as gs_submit_choice, get_state as gs_get_state, reset_state as gs_reset_state
from django.views.decorators.http import require_POST

from rag.retrieve import retrieve_chunks

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'data', 'static_stories.json')

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    story_data = json.load(f)

# --- helper method ---
def get_entry_by_year(year):
    return next((item for item in story_data if str(item["year"]) == str(year)), None)


def get_story_scenario(request):

    """
    Retrieve the background information for a given year from the story data.
    Expects a 'year' parameter in the GET request.
    Returns a JSON response with the background or an error message.
    """
    year = request.GET.get('year')
    if not year:
        return HttpResponseBadRequest("Missing 'year' parameter.")

    entry = get_entry_by_year(year)
    if not entry:
        return JsonResponse({"error": "Year not found."}, status=404)

    return JsonResponse({
        "year": entry["year"],
        "scenario": entry["background"]
    })


def get_story_question(request):

    """
    Retrieve the question for a given year from the story data.
    Expects a 'year' parameter in the GET request.
    Returns a JSON response with the question or an error message.
    """
    year = request.GET.get('year')
    if not year:
        return HttpResponseBadRequest("Missing 'year' parameter.")

    entry = get_entry_by_year(year)
    if not entry:
        return JsonResponse({"error": "Year not found."}, status=404)

    return JsonResponse({
        "year": entry["year"],
        "question": entry["question"],
        "options": entry["options"]
    })

"""
What is this function supposed to do??? 
currently it is sending the same question back so not using it 
"""
def get_story_result_by_choice(request):

    """
    Retrieve the result of a user's choice for a given year from the story data.
    Expects 'year' and 'choice' parameters in the GET request.
    Returns a JSON response with the result, or an error message if not found.
    """
    year = request.GET.get('year')
    choice = request.GET.get('choice')
    if not year or not choice:
        return HttpResponseBadRequest("Missing 'year' or 'choice' parameter.")

    entry = next((item for item in story_data if str(item["year"]) == year), None)
    if not entry:
        return JsonResponse({"error": "Year not found."}, status=404)
    
    result = entry.get("options", {}).get(choice.lower())
    if not result:
        return JsonResponse({"error": f"No result found for choice '{choice}'"}, status=404)

    return JsonResponse({
        "year": entry["year"],
        "choice": choice,
        "result": result,
        "next_year": entry["year"] + 1
    })


def get_story_result(request):
    """
    Retrieves the user's selected choice for a given question. This is a post method 
    which means this is directly retrived from the user input
    """
    if request.method == "POST":
        year = request.get("year")
        choice = request.get("choice")

    if not year or not choice:
        return HttpResponseBadRequest("Missing 'year' or 'choice' parameter.")

    return JsonResponse({
        "year": year,
        "choice": choice,
    })


@csrf_exempt
def rag_retrieve(request):
    
    default_query = "fatigue"
    query: str
    if request.method != 'POST':
        logger.warning("Non-POST request received. Using default query instead")
        query = default_query
    else:
        query_text = request.POST.get('query_text')
        keywords = request.POST.get('keywords')
        query = query_text or keywords
        if not query:
            logger.warning("No 'query_text' or 'keywords' parameter provided. Using default query instead")
            query = default_query

    items = retrieve_chunks(query)
    return JsonResponse({'items': items})

@csrf_exempt
@require_POST
def get_story_result(request):
    """
    NEW: Multiplayer-aware choice submit.
    - Accepts JSON: { "year": <int>, "choice": "<optionId>", "clientId": "<string>", "players": <int optional> }
    - Returns:
      {
        "year": <currentYear>,
        "choiceAccepted": true,
        "decided": <bool>,
        "decidedOption": "<optionId or null>",
        "next_year": <int or null>,
        "counts": {"yes": 1, "no": 1, ...},
        "needed": <int>  # how many choices required to decide this round (for info)
      }
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    choice = body.get("choice")
    # Optional: client identifier; if absent, we fallback to a coarse token
    client_id = body.get("clientId")
    if not client_id:
        # coarse fallback: IP + UA; better to pass a real device token from the client
        client_id = f"{request.META.get('REMOTE_ADDR','anon')}:{request.META.get('HTTP_USER_AGENT','ua')}"

    # Optional: hint how many players you expect (1 or 2); default 2
    players_hint = body.get("players", 2)
    try:
        players_hint = int(players_hint)
    except Exception:
        players_hint = 2
    players_hint = max(1, min(players_hint, 8))

    if not choice:
        return HttpResponseBadRequest("Missing 'choice'.")

    # Drive the single-room state machine
    result = gs_submit_choice(client_id=client_id, choice=choice, connected_players_hint=players_hint)

    # Compose response
    resp = {
        "choiceAccepted": True,
        "decided": bool(result.get("decided")),
        "decidedOption": result.get("decidedOption"),
        "year": result.get("year"),
        "next_year": result.get("next_year"),
        "counts": result.get("counts", {}),
        "needed": result.get("needed", None),
        "done": result.get("done", False),
    }
    return JsonResponse(resp)


def get_story_state(request):
    """
    NEW: Lightweight state for polling (for host icons).
    Returns current year, question, options, and anonymous per-option counts.
    """
    return JsonResponse(gs_get_state())

def reset_story(request):
    """
    OPTIONAL: Dev helper to reset the in-memory state.
    """
    gs_get_state()  # just to ensure module is loaded
    gs_reset_state()
    return JsonResponse({"ok": True})