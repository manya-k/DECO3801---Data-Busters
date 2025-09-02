# api/game_state.py
import json, threading, random
from pathlib import Path
from django.conf import settings

DATA_DIR = Path(__file__).resolve().parent / "data"
STORIES_PATH = DATA_DIR / "static_stories.json"
DECISIONS_PATH = DATA_DIR / "decisions.json"

with STORIES_PATH.open("r", encoding="utf-8") as f:
    STORY = json.load(f)

_lock = threading.RLock()
STATE = {
    "current_index": 0,          # which entry in STORY we are on
    "choices": {},               # client_id -> option_id (e.g., "yes"/"no")
}

def _need_choices(connected_count: int = 2) -> int:
    """Require MIN_CHOICES_TO_DECIDE, but scale down to available players (min 1)."""
    want = getattr(settings, "MIN_CHOICES_TO_DECIDE", 2)
    # you can wire a real 'connected' count later; default assume 2
    return min(want, max(1, connected_count))

def current_story():
    idx = STATE["current_index"]
    return STORY[idx] if 0 <= idx < len(STORY) else None

def option_counts():
    counts = {}
    for opt in STATE["choices"].values():
        counts[opt] = counts.get(opt, 0) + 1
    return counts

def _load_decisions():
    if not DECISIONS_PATH.exists():
        return []
    try:
        return json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []

def _save_decision(record: dict):
    DECISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        arr = _load_decisions()
        arr.append(record)
        DECISIONS_PATH.write_text(json.dumps(arr, indent=2), encoding="utf-8")
        tmp = DECISIONS_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(arr, indent=2), encoding="utf-8")
        tmp.replace(DECISIONS_PATH)

def submit_choice(client_id: str, choice: str, connected_players_hint: int = 2):
    """
    Record a client's choice for the CURRENT story year.
    Returns a dict describing whether the round is decided, and counts.
    """
    with _lock:
        story = current_story()
        if not story:
            return {"decided": False, "counts": {}, "done": True}

        # Record/overwrite this client's choice
        STATE["choices"][client_id] = str(choice).lower()

        counts = option_counts()
        needed = _need_choices(connected_players_hint)

        if len(STATE["choices"]) < needed:
            # Not enough choices yet
            return {
                "decided": False,
                "counts": counts,
                "year": story["year"],
                "question": story["question"],
                "needed": needed,
            }

        # Decide: if all same → that option; else random among chosen options
        chosen = set(STATE["choices"].values())
        decided = next(iter(chosen)) if len(chosen) == 1 else random.choice(list(chosen))

        # Persist
        record = {
            "roomId": getattr(settings, "MUSEUM_ROOM_ID", "MUSEUM"),
            "year": story["year"],
            "question": story["question"],
            "decidedOption": decided,
            "optionCounts": counts,
        }
        _save_decision(record)

        # Advance year
        STATE["current_index"] += 1
        STATE["choices"].clear()

        next_story = current_story()
        return {
            "decided": True,
            "decidedOption": decided,
            "counts": counts,
            "year": story["year"],
            "next_year": next_story["year"] if next_story else None,
            "done": next_story is None,
        }

def get_state():
    """Expose current year, counts, and basic info for polling from host."""
    with _lock:
        story = current_story()
        return {
            "index": STATE["current_index"],
            "year": story["year"] if story else None,
            "question": story["question"] if story else None,
            "options": story["options"] if story else None,
            "counts": option_counts(),
            "has_next": (STATE["current_index"] + 1) < len(STORY),
        }

def reset_state():
    with _lock:
        STATE["current_index"] = 0
        STATE["choices"].clear()
