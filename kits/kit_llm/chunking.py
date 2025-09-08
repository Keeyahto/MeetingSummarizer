from __future__ import annotations

from typing import Dict, List

from .token_utils import count_tokens_text


def segments_to_lines(segments: List[Dict]) -> List[str]:
    lines: List[str] = []
    for seg in segments or []:
        sp = seg.get("speaker", "Участник")
        tx = seg.get("text", "")
        if not tx:
            continue
        lines.append(f"{sp}: {tx}")
    return lines


def chunk_by_token_budget(lines: List[str], budget_tokens: int) -> List[str]:
    if budget_tokens <= 0:
        return ["\n".join(lines)] if lines else []
    chunks: List[str] = []
    cur: List[str] = []
    cur_tokens = 0
    for ln in lines:
        ln_tokens = count_tokens_text(ln) + 1  # account for newline
        if cur and cur_tokens + ln_tokens > budget_tokens:
            chunks.append("\n".join(cur))
            cur = []
            cur_tokens = 0
        cur.append(ln)
        cur_tokens += ln_tokens
    if cur:
        chunks.append("\n".join(cur))
    return chunks

