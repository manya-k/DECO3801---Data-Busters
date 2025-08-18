import json
import os
from django.http import JsonResponse, HttpResponseBadRequest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'data', 'static_stories.json')

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    story_data = json.load(f)

def get_story_background(request):
    year = request.GET.get('year')
    if not year:
        return HttpResponseBadRequest("Missing 'year' parameter.")

    entry = next((item for item in story_data if str(item["year"]) == year), None)
    if not entry:
        return JsonResponse({"error": "Year not found."}, status=404)

    return JsonResponse({
        "year": entry["year"],
        "background": entry["background"]
    })


def get_story_question(request):
    year = request.GET.get('year')
    if not year:
        return HttpResponseBadRequest("Missing 'year' parameter.")

    entry = next((item for item in story_data if str(item["year"]) == year), None)
    if not entry:
        return JsonResponse({"error": "Year not found."}, status=404)

    return JsonResponse({
        "year": entry["year"],
        "question": entry["question"]
    })


def get_story_result_by_choice(request):
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