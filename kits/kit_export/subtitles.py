from typing import List, Dict
from kits.utils.text import srt_timestamp, vtt_timestamp


def words_to_caption_lines(words: List[Dict], max_chars: int = 55):
    # Greedy grouping of words into lines with timestamps
    items = []
    cur_text = []
    cur_start = None
    last_end = None
    for w in words:
        t = w.get("text", "").strip()
        if not t:
            continue
        start = float(w.get("start", 0))
        end = float(w.get("end", start))
        if cur_start is None:
            cur_start = start
        prospective = (" ".join(cur_text + [t])).strip()
        if len(prospective) > max_chars and cur_text:
            items.append({"start": cur_start, "end": last_end or end, "text": " ".join(cur_text)})
            cur_text = [t]
            cur_start = start
        else:
            cur_text.append(t)
        last_end = end
    if cur_text:
        items.append({"start": cur_start or 0, "end": last_end or (cur_start or 0) + 1, "text": " ".join(cur_text)})
    return items


def build_srt(words: List[Dict]) -> str:
    lines = words_to_caption_lines(words)
    blocks = []
    for i, it in enumerate(lines, start=1):
        ts = f"{srt_timestamp(it['start'])} --> {srt_timestamp(it['end'])}"
        blocks.append(f"{i}\n{ts}\n{it['text']}\n")
    return "\n".join(blocks).strip() + "\n"


def build_vtt(words: List[Dict]) -> str:
    lines = words_to_caption_lines(words)
    out = ["WEBVTT\n"]
    for it in lines:
        ts = f"{vtt_timestamp(it['start'])} --> {vtt_timestamp(it['end'])}"
        out.append(f"{ts}\n{it['text']}\n\n")
    return "".join(out)

