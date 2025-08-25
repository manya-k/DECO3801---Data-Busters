# Minimal turn controller for: LLM + RAG (two-step) + Image + State memory
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time, hashlib, json


# ---------- Data models ----------
@dataclass
class ContextMeta:
    doc_id: str
    title: str
    source: str
    year: Optional[int] = None
    tags: Optional[List[str]] = None


@dataclass
class ContextItem:
    text: str
    score: float
    meta: ContextMeta


@dataclass
class ImageBrief:
    subject: str
    scene: str
    mood: str
    style: str


@dataclass
class TurnOutput:
    question: str
    options: List[str]
    choice: str
    narrative: str
    image_brief: ImageBrief
    contexts_question: List[ContextItem] = field(default_factory=list)
    contexts_description: List[ContextItem] = field(default_factory=list)
    took_ms_retrieval_a: int = 0
    took_ms_retrieval_b: int = 0


@dataclass
class StateMemory:
    year: int
    characters: List[Dict[str, Any]] = field(default_factory=list)
    facts: List[str] = field(default_factory=list)
    pending_threads: List[str] = field(default_factory=list)
    choices_history: List[Dict[str, Any]] = field(default_factory=list)


# ---------- Client interfaces (replace Mock with real ones) ----------
class RagClient:
    """HTTP wrapper to your RAG service (/rag/retrieve). Replace .retrieve() later."""
    def retrieve(self, *, query_text: str, keywords: List[str] | None = None,
                 k: int = 4, min_score: float = 0.25, filters: Dict[str, Any] | None = None
                 ) -> List[ContextItem]:
        raise NotImplementedError


class LlmClient:
    """Wrapper to your local LLM (Ollama, etc.). Replace .generate_* later."""
    def generate_question_and_options(self, *, year: int, last_desc: str,
                                     contexts: List[ContextItem],
                                     state: StateMemory) -> Dict[str, Any]:
        raise NotImplementedError

    def generate_description(self, *, year: int, last_desc: str, question: str,
                             choice: str, contexts: List[ContextItem],
                             state: StateMemory) -> Dict[str, Any]:
        raise NotImplementedError


class ImageClient:
    """Send ImageBrief to image pipeline (ComfyUI/SD)."""
    def enqueue(self, brief: ImageBrief) -> str:
        raise NotImplementedError


# ---------- Query builders ----------
def build_query_from_last_story(last_desc: str) -> Dict[str, Any]:
    """Very simple rules-based extractor. Swap for smarter version later."""
    # keep 1–2 sentences
    query_text = last_desc.strip()[:600]

    # naive keyword picks: nouns / capitalized tokens / year-like
    import re
    candidates = re.findall(r"[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)?|20\d{2}|memory|erasure|audit|ethic|policy|neuro",
                            last_desc, flags=re.IGNORECASE)
    # de-dup & normalize
    seen, keywords = set(), []
    for tok in candidates:
        t = tok.lower()
        if t not in seen and 3 <= len(t) <= 40:
            keywords.append(t)
            seen.add(t)
        if len(keywords) >= 5:
            break
    return {"query_text": query_text, "keywords": keywords}


def build_query_from_option(option_text: str, last_desc: str) -> Dict[str, Any]:
    """Focus retrieval on the chosen option; merge a short seed from last_desc."""
    seed = (option_text + " ; " + last_desc[:200]).strip()
    base = build_query_from_last_story(seed)
    base["query_text"] = seed[:600]
    return base


# ---------- Prompt helpers (LLM-facing composition) ----------
def compose_context_block(items: List[ContextItem]) -> str:
    lines = []
    for i, it in enumerate(items[:8], 1):
        m = it.meta
        lines.append(f"({i}) {it.text} [title:{m.title}, source:{m.source}, year:{m.year}]")
    return "\n".join(lines)


# ---------- Orchestrator ----------
class TurnEngine:
    def __init__(self, rag: RagClient, llm: LlmClient, img: ImageClient):
        self.rag, self.llm, self.img = rag, llm, img

    def play_round(self, *, state: StateMemory, last_desc: str,
                   k_a: int = 4, k_b: int = 4, min_score: float = 0.25) -> TurnOutput:
        # 1) Query A for question/options
        q1 = build_query_from_last_story(last_desc)
        t0 = time.time()
        ctx_a = self._dedup_by_doc(self.rag.retrieve(
            query_text=q1["query_text"], keywords=q1["keywords"], k=k_a, min_score=min_score))
        t1 = time.time()

        # 2) LLM → question + options
        qa = self.llm.generate_question_and_options(
            year=state.year, last_desc=last_desc, contexts=ctx_a, state=state)
        question: str = qa["question"].strip()
        options: List[str] = [o.strip() for o in qa["options"]][:4]
        if not options:
            # fallback: generate a yes/no if options missing
            options = ["Yes", "No"]

        # 3) (UI) choose one option – for demo we pick index 0; replace with actual choice
        choice = qa.get("selected_option", options[0])

        # 4) Query B focused by chosen option
        q2 = build_query_from_option(choice, last_desc)
        t2 = time.time()
        ctx_b = self._dedup_by_doc(self.rag.retrieve(
            query_text=q2["query_text"], keywords=q2["keywords"], k=k_b, min_score=min_score))
        t3 = time.time()

        # 5) LLM → description + image brief
        desc = self.llm.generate_description(
            year=state.year, last_desc=last_desc, question=question,
            choice=choice, contexts=ctx_b, state=state)
        narrative: str = desc["narrative"].strip()
        ib = desc["image_brief"]
        image_brief = ImageBrief(**ib)

        # 6) send image (async placeholder)
        image_id = self.img.enqueue(image_brief)  # you may store/return this id

        # 7) update memory (very minimal)
        state.choices_history.append({
            "year": state.year, "question": question, "choice": choice,
            "context_doc_ids": [c.meta.doc_id for c in ctx_b]
        })
        # Optionally push new facts inferred from narrative
        if narrative:
            state.facts.append(narrative[:140])

        return TurnOutput(
            question=question, options=options, choice=choice,
            narrative=narrative, image_brief=image_brief,
            contexts_question=ctx_a, contexts_description=ctx_b,
            took_ms_retrieval_a=int((t1 - t0) * 1000),
            took_ms_retrieval_b=int((t3 - t2) * 1000),
        )

    @staticmethod
    def _dedup_by_doc(items: List[ContextItem]) -> List[ContextItem]:
        seen, out = set(), []
        for it in items:
            if it.meta.doc_id not in seen:
                out.append(it)
                seen.add(it.meta.doc_id)
        return out


# ---------- Mock implementations (for local testing now) ----------
class MockRag(RagClient):
    def __init__(self):
        # tiny in-memory corpus
        self.corpus = [
            ("doc:ethics2030", "Neuroethics Review 2030", "neuro_ethics.pdf",
             2030, "Consent audits for memory erasure in clinical settings."),
            ("doc:policy2035", "Policy Draft 2035", "gov_policy.pdf",
             2035, "Government regulation on fatigue-related memory erasure."),
            ("doc:cloud2040", "MemoryCloud Whitepaper", "cloud_wp.pdf",
             2040, "Commercial memory storage risks and audit mechanisms."),
        ]

    def retrieve(self, *, query_text: str, keywords: List[str] | None = None,
                 k: int = 4, min_score: float = 0.0, filters: Dict[str, Any] | None = None
                 ) -> List[ContextItem]:
        # very naive scoring: keyword hit count
        keyset = set((keywords or []) + query_text.lower().split())
        scored = []
        for doc_id, title, src, year, text in self.corpus:
            score = sum(1 for w in keyset if w in text.lower()) / 5.0
            if score >= min_score:
                meta = ContextMeta(doc_id=doc_id, title=title, source=src, year=year)
                scored.append(ContextItem(text=text, score=score, meta=meta))
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:k]


class MockLLM(LlmClient):
    def generate_question_and_options(self, *, year: int, last_desc: str,
                                     contexts: List[ContextItem],
                                     state: StateMemory) -> Dict[str, Any]:
        ctx = compose_context_block(contexts)
        # minimal deterministic output
        question = f"In {year}, should consent audits be expanded to fatigue-related memory erasure?"
        options = [
            "Expand audits under limited government oversight",
            "Keep audits private within clinics",
            "Pause all fatigue-related erasure until ethics board review"
        ]
        return {"question": question, "options": options, "selected_option": options[0]}

    def generate_description(self, *, year: int, last_desc: str, question: str,
                             choice: str, contexts: List[ContextItem],
                             state: StateMemory) -> Dict[str, Any]:
        ctx = compose_context_block(contexts)
        narrative = (
            f"{year}: A joint taskforce pilots consent audits for fatigue‑linked erasures. "
            f"Under '{choice}', clinics log each procedure to a local ledger referencing "
            f"[{contexts[0].meta.title}, {contexts[0].meta.year}] where available."
        )
        image_brief = {
            "subject": "clinic audit desk",
            "scene": "neural clinic with consent terminals and wall poster 'Consent Audit'",
            "mood": "sober, clinical",
            "style": "documentary, mid‑shot"
        }
        return {"narrative": narrative, "image_brief": image_brief}


class MockImage(ImageClient):
    def enqueue(self, brief: ImageBrief) -> str:
        key = json.dumps(brief.__dict__, sort_keys=True).encode("utf-8")
        return hashlib.md5(key).hexdigest()


# ---------- Example usage ----------
if __name__ == "__main__":
    state = StateMemory(year=2037)
    last_desc = ("In 2036, memory clinics reported rising demand for fatigue‑related erasure. "
                 "Civil groups questioned consent transparency; regulators drafted audit guidelines.")
    engine = TurnEngine(rag=MockRag(), llm=MockLLM(), img=MockImage())
    out = engine.play_round(state=state, last_desc=last_desc)

    print("Q:", out.question)
    print("Options:", out.options)
    print("Chosen:", out.choice)
    print("Narrative:", out.narrative)
    print("Image brief:", out.image_brief)
    print("RAG A took(ms):", out.took_ms_retrieval_a, "RAG B took(ms):", out.took_ms_retrieval_b)