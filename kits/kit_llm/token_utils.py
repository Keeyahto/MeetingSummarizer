from __future__ import annotations

import re
from typing import List, Dict


_ENC = None


def _load_tiktoken():
    global _ENC
    if _ENC is not None:
        return _ENC
    try:
        import tiktoken  # type: ignore

        # Generic encoding; accuracy is not critical, we just need a budget guardrail.
        _ENC = tiktoken.get_encoding("cl100k_base")
    except Exception:
        _ENC = None
    return _ENC


def count_tokens_text(text: str) -> int:
    enc = _load_tiktoken()
    if enc is not None:
        try:
            return len(enc.encode(text))
        except Exception:
            pass
    # Fallback heuristic: ~4 chars per token
    # Add a bit of penalty for punctuation/whitespace variety
    return max(1, int(len(text) / 4))


def count_tokens_messages(messages: List[Dict[str, str]]) -> int:
    # Very rough: sum of content + role labels overhead
    total = 0
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        total += count_tokens_text(role) + count_tokens_text(content) + 4
    return total

