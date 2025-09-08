from __future__ import annotations

import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

from kits.kit_common.config import settings
from kits.kit_common.paths import ensure_job_dirs, write_json
from kits.utils.audio import probe_duration_sec
from kits.kit_asr.whisperx_asr import transcribe_with_whisperx, pseudo_diarize
from kits.kit_llm.openai_backend import summarize_transcript
from kits.kit_export.subtitles import build_srt, build_vtt
from kits.kit_export.minutes import build_minutes_md


def build_paragraphs(segments: List[Dict]) -> List[Dict]:
    # Merge word-level segments by speaker and pause
    paras = []
    cur = None
    last_end = 0.0
    for seg in segments:
        sp = seg.get("speaker") or "Участник 1"
        start = float(seg.get("start", 0))
        end = float(seg.get("end", start))
        txt = seg.get("text", "").strip()
        wrds = seg.get("words") or []
        if (cur and (sp != cur["speaker"] or start - last_end >= 0.5)):
            paras.append(cur)
            cur = None
        if not cur:
            cur = {"speaker": sp, "start": start, "end": end, "text": txt, "words": wrds[:]}
        else:
            cur["end"] = end
            cur["text"] = (cur["text"] + " " + txt).strip()
            cur["words"].extend(wrds)
        last_end = end
    if cur:
        paras.append(cur)
    return paras


def compute_metrics(paragraphs: List[Dict]) -> Dict:
    # speech rate (words/min), talk time share, pauses count (simple proxy)
    total_dur = sum(max(0.0, p["end"] - p["start"]) for p in paragraphs) or 1.0
    talk_time = defaultdict(float)
    words_total = 0
    pauses = 0
    prev_end = 0.0
    for p in paragraphs:
        dur = max(0.0, p["end"] - p["start"]) 
        talk_time[p["speaker"]] += dur
        words_total += len((p.get("text") or "").split())
        if p["start"] - prev_end >= 0.5:
            pauses += 1
        prev_end = p["end"]
    speech_rate = (words_total / (total_dur / 60.0)) if total_dur > 0 else 0.0
    total_t = sum(talk_time.values()) or 1.0
    talk_share = {k: round(v / total_t, 2) for k, v in talk_time.items()}
    return {
        "speech_rate_wpm": round(speech_rate, 1),
        "talk_time": talk_share,
        "pauses_count": pauses,
    }


def extract_keywords(paragraphs: List[Dict], top_k: int = 20) -> List[str]:
    stop = set("""
        a an the and or but if in into on at by for with of to from as is are was were be been being this that those these it its it's i you he she we they them us our your my me him her their
        и в во не что он на я с со как а то все она так его но о из у за для от по а к до это эту этой эти этот ещё уже бы же ли или либо либо-то ни да нет при мы вы их чем чем-то чтоб чтобы тот та те кто где когда куда откуда почему потому также также-то
    """.split())
    words = []
    for p in paragraphs:
        for w in (p.get("text") or "").lower().split():
            w = ''.join(ch for ch in w if ch.isalnum() or ch in ('-', '_'))
            if w and w not in stop and not w.isdigit() and len(w) > 2:
                words.append(w)
    freq = Counter(words)
    return [w for w, _ in freq.most_common(top_k)]


def run_pipeline(payload: Dict):
    import logging
    logger = logging.getLogger(__name__)
    
    job_id = payload["job_id"]
    input_path = Path(payload["input_path"])  # original
    fast_mode = bool(payload.get("fast_mode", False))
    language = payload.get("language")

    logger.info(f"Запуск pipeline для задачи {job_id}")
    logger.info(f"Входной файл: {input_path}")
    logger.info(f"Быстрый режим: {fast_mode}")
    logger.info(f"Язык: {language}")

    paths = ensure_job_dirs(job_id)
    work_wav = paths["work_dir"] / "normalized.wav"
    duration = probe_duration_sec(work_wav)
    logger.info(f"Длительность аудио: {duration:.1f} секунд")

    # ASR + alignment (+ diarization)
    logger.info("Начало транскрипции с WhisperX")
    try:
        asr = transcribe_with_whisperx(work_wav, language=language)
        logger.info("Транскрипция завершена успешно")
    except Exception as e:
        logger.error(f"Ошибка при транскрипции: {str(e)}", exc_info=True)
        raise
    segments = asr.get("segments", [])
    # If diarization disabled or missing speaker tags, apply pseudo
    if fast_mode or not any(s.get("speaker") for s in segments):
        segments = pseudo_diarize(segments)

    # Paragraphs and metrics
    paragraphs = build_paragraphs(segments)
    metrics = compute_metrics(paragraphs)
    speakers = sorted(list({p["speaker"] for p in paragraphs}))

    # Topics (optional, fast_mode skip). Placeholder: none
    topics = [] if fast_mode else []

    transcript = {
        "job_id": job_id,
        "language": asr.get("language"),
        "duration_sec": duration,
        "speakers": speakers,
        "metrics": metrics,
        "segments": [
            {
                "start": p["start"],
                "end": p["end"],
                "speaker": p["speaker"],
                "text": p["text"],
                "words": p.get("words", []),
            }
            for p in paragraphs
        ],
        "keywords": extract_keywords(paragraphs),
        "topics": topics,
    }

    # Summarize via LLM
    summary = summarize_transcript(transcript)

    out_dir = paths["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "transcript.json", transcript)
    write_json(out_dir / "summary.json", summary)

    # Subtitles from words
    all_words = []
    for p in paragraphs:
        all_words.extend(p.get("words", []))
    if all_words:
        (out_dir / "subs.srt").write_text(build_srt(all_words), encoding="utf-8")
        (out_dir / "subs.vtt").write_text(build_vtt(all_words), encoding="utf-8")

    # Minutes MD + JSON
    md = build_minutes_md(transcript, summary)
    (out_dir / "minutes.md").write_text(md, encoding="utf-8")
    write_json(out_dir / "minutes.json", {"transcript": transcript, "summary": summary})

    return {
        "job_id": job_id,
        "language": transcript.get("language"),
        "duration_sec": transcript.get("duration_sec"),
        "speakers": speakers,
        "metrics": metrics,
        "out": {
            "transcript_json": str((out_dir / "transcript.json").resolve()),
            "summary_json": str((out_dir / "summary.json").resolve()),
            "minutes_md": str((out_dir / "minutes.md").resolve()),
            "minutes_json": str((out_dir / "minutes.json").resolve()),
            "srt": str((out_dir / "subs.srt").resolve()),
            "vtt": str((out_dir / "subs.vtt").resolve()),
        },
    }

