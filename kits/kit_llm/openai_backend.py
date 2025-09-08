from typing import Dict, Generator, List
import json
from openai import OpenAI, BadRequestError
from kits.kit_common.config import settings
from .token_utils import count_tokens_messages, count_tokens_text
from .chunking import segments_to_lines, chunk_by_token_budget


def _client() -> OpenAI:
    return OpenAI(base_url=settings.OPENAI_BASE_URL, api_key=settings.OPENAI_API_KEY)


def _build_messages_for_summary(chunks: List[str]) -> List[Dict[str, str]]:
    sys = (
        "Ты эксперт по анализу и резюмированию встреч. Извлеки краткое резюме (5-7 предложений), "
        "пункты действий (с необязательным ответственным и сроком), решения и риски. "
        "Отвечай ТОЛЬКО на русском языке. "
        "Верни JSON поля: tldr, action_items[{text, owner, due}], decisions[], risks[]."
    )
    # Assemble a single prompt from chunks
    content = "\n\n".join(chunks)
    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": content},
    ]


def summarize_transcript(transcript: dict) -> dict:
    # Simple strategy: single pass; callers can pre-chunk if needed
    text = []
    for seg in transcript.get("segments", []) or []:
        sp = seg.get("speaker", "Участник")
        tx = seg.get("text", "")
        text.append(f"{sp}: {tx}")
    joined = "\n".join(text)
    msgs = _build_messages_for_summary([joined])
    client = _client()
    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=msgs,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "meeting_summary",
                "schema": {
                    "type": "object",
                    "properties": {
                        "tldr": {"type": "string"},
                        "action_items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                    "owner": {"type": "string"},
                                    "due": {"type": "string"}
                                }
                            }
                        },
                        "decisions": {"type": "array", "items": {"type": "string"}},
                        "risks": {"type": "array", "items": {"type": "string"}}
                    }
                }
            }
        },
    )
    out = resp.choices[0].message.content or "{}"
    try:
        data = json.loads(out)
    except Exception:
        data = {"tldr": out}
    # Best-effort token usage
    try:
        data["_tokens_used"] = resp.usage.total_tokens  # type: ignore[attr-defined]
    except Exception:
        pass
    return data


def _schema() -> Dict:
    return {
        "type": "object",
        "properties": {
            "tldr": {"type": "string"},
            "action_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "owner": {"type": "string"},
                        "due": {"type": "string"},
                    },
                },
            },
            "decisions": {"type": "array", "items": {"type": "string"}},
            "risks": {"type": "array", "items": {"type": "string"}},
        },
    }


def summarize_transcript_iterative(transcript: dict) -> dict:
    # Map -> Reduce with rolling JSON state
    lines = segments_to_lines(transcript.get("segments", []) or [])

    # Budgets: keep chunks well below LLM_MAX_TOKENS to leave room for state/system
    # Estimate dynamic budget: ~70% of LLM_MAX_TOKENS minus current state
    def build_system_prompt() -> str:
        return (
            "Ты эксперт по анализу и резюмированию встреч. Тебе даются: "
            "1) текущее состояние сводки (JSON по схеме), 2) новая часть стенограммы. "
            "Обнови и верни ПОЛНЫЙ JSON по схеме: tldr, action_items[{text, owner, due}], decisions[], risks[]. "
            "Отвечай ТОЛЬКО валидным JSON и ТОЛЬКО на русском языке."
        )

    state: Dict = {"tldr": "", "action_items": [], "decisions": [], "risks": []}
    system_prompt = build_system_prompt()

    # Start with conservative chunk budget
    base_budget = max(256, int(settings.LLM_MAX_TOKENS * 0.7))

    chunks: List[str] = []
    # Initial overhead estimate (system + empty state)
    overhead = count_tokens_text(system_prompt) + count_tokens_text(json.dumps(state, ensure_ascii=False)) + 64
    chunk_budget = max(128, base_budget - overhead)
    chunks = chunk_by_token_budget(lines, chunk_budget)

    client = _client()
    schema = _schema()

    for idx, chunk in enumerate(chunks):
        # Recompute dynamic budget as state grows for safety (no direct use here, but we can rebuild system if needed)
        overhead = count_tokens_text(system_prompt) + count_tokens_text(json.dumps(state, ensure_ascii=False)) + 64
        # Build messages
        msgs = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Текущее состояние (JSON):\n{json.dumps(state, ensure_ascii=False)}"},
            {"role": "user", "content": f"Новая часть стенограммы:\n{chunk}"},
        ]

        try:
            resp = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=msgs,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "meeting_summary", "schema": schema},
                },
            )
        except BadRequestError:
            # Try looser format if backend rejects json_schema
            resp = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=msgs + [{"role": "system", "content": "Верни ТОЛЬКО валидный JSON без пояснений."}],
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                response_format={"type": "json_object"},
            )

        txt = resp.choices[0].message.content or "{}"
        try:
            new_state = json.loads(txt)
        except Exception:
            new_state = _format_text_to_json(txt)
        if isinstance(new_state, dict):
            state = _merge_states(state, new_state)

    # Optional small refine pass: ask to tidy the JSON
    try:
        refine_msgs = [
            {"role": "system", "content": (
                "Приведи итоговую сводку к аккуратному и краткому виду. "
                "Верни ТОЛЬКО валидный JSON по схеме. Текст на русском."
            )},
            {"role": "user", "content": json.dumps(state, ensure_ascii=False)},
        ]
        resp = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=refine_msgs,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            response_format={"type": "json_object"},
        )
        txt = resp.choices[0].message.content or "{}"
        try:
            new_state = json.loads(txt)
        except Exception:
            new_state = _format_text_to_json(txt)
        if isinstance(new_state, dict):
            state = _merge_states(state, new_state)
    except Exception:
        pass

    return _sanitize_state(state)


def _merge_states(a: Dict, b: Dict) -> Dict:
    # Merge TL;DR with preference to newer, keep both succinctly
    tldr = (b.get("tldr") or "").strip()
    if not tldr:
        tldr = (a.get("tldr") or "").strip()

    def _norm_list(x):
        return [i for i in (x or []) if i]

    def _dedup_str_list(lst: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for s in lst:
            if s not in seen:
                out.append(s)
                seen.add(s)
        return out

    def _dedup_items(lst: List[Dict]) -> List[Dict]:
        seen = set()
        out = []
        for it in lst:
            key = (it.get("text", ""), it.get("owner", ""), it.get("due", ""))
            if key not in seen:
                out.append(it)
                seen.add(key)
        return out

    action_items = _dedup_items(_norm_list(a.get("action_items")) + _norm_list(b.get("action_items")))
    decisions = _dedup_str_list(_norm_list(a.get("decisions")) + _norm_list(b.get("decisions")))
    risks = _dedup_str_list(_norm_list(a.get("risks")) + _norm_list(b.get("risks")))

    return {
        "tldr": tldr,
        "action_items": action_items,
        "decisions": decisions,
        "risks": risks,
    }


def _format_text_to_json(text: str) -> Dict:
    """Best-effort conversion of free-form text into our JSON schema using the same model.
    If model still returns non-JSON, fallback to minimal JSON with tldr trimmed.
    """
    client = _client()
    prompt = (
        "Преобразуй следующий русский текст в JSON со строгими полями: \n"
        "tldr (5-7 предложений), action_items (массив объектов {text, owner, due}), "
        "decisions (массив строк), risks (массив строк). Ответь ТОЛЬКО JSON."
    )
    msgs = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": text},
    ]
    try:
        resp = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=msgs,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            response_format={"type": "json_object"},
        )
        out = resp.choices[0].message.content or "{}"
        return json.loads(out)
    except Exception:
        pass

    # Fallback minimal JSON
    return _sanitize_state({"tldr": text})


def _sanitize_state(state: Dict) -> Dict:
    # Ensure structure and brevity
    if not isinstance(state, dict):
        state = {}
    tldr = state.get("tldr") or ""
    tldr = _limit_sentences(tldr, max_sentences=7)
    ai = state.get("action_items") or []
    if not isinstance(ai, list):
        ai = []
    decisions = state.get("decisions") or []
    if not isinstance(decisions, list):
        decisions = []
    risks = state.get("risks") or []
    if not isinstance(risks, list):
        risks = []
    return {
        "tldr": tldr,
        "action_items": ai,
        "decisions": decisions,
        "risks": risks,
    }


def _limit_sentences(text: str, max_sentences: int = 7) -> str:
    s = text.strip()
    if not s:
        return s
    # naive split on Russian/English punctuation
    import re
    parts = re.split(r"(?<=[\.!?])\s+", s)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) <= max_sentences:
        return " ".join(parts)
    return " ".join(parts[:max_sentences])


def stream_tldr(transcript: dict) -> Generator[str, None, None]:
    # Stream only TL;DR tokens
    text = []
    for seg in transcript.get("segments", []) or []:
        sp = seg.get("speaker", "Участник")
        tx = seg.get("text", "")
        text.append(f"{sp}: {tx}")
    joined = "\n".join(text)

    system = "Ты эксперт по анализу и резюмированию встреч. Отвечай ТОЛЬКО на русском языке. Верни только краткое резюме (TL;DR) текста."
    msgs = [
        {"role": "system", "content": system},
        {"role": "user", "content": joined},
    ]
    client = _client()
    with client.chat.completions.stream(
        model=settings.LLM_MODEL,
        messages=msgs,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
    ) as stream:
        for event in stream:
            if event.type == "token":
                yield event.token
