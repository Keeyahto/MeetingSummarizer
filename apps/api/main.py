import os
import uuid
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from kits.kit_common.config import settings
from kits.kit_common.errors import http_error_response, APIError
from kits.kit_common.paths import (
    ensure_job_dirs,
    job_paths,
    read_json,
    write_json,
    within_data_dir,
)
from kits.utils.audio import (
    is_supported_ext,
    normalize_audio,
    probe_duration_sec,
)
from kits.kit_pipeline.pipeline import run_pipeline

try:
    import torch  # type: ignore
except Exception:  # pragma: no cover
    torch = None


app = FastAPI(title="Meeting Summarizer API")

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.CORS_ORIGINS == "*" else settings.CORS_ORIGINS.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.exception_handler(APIError)
async def api_error_handler(_: Request, exc: APIError):
    logger.error(f"API Error: {exc.code} - {exc.type} - {exc.message}")
    return http_error_response(exc.code, exc.type, exc.message)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return http_error_response(500, "internal_error", f"Internal server error: {str(exc)}")


@app.get("/health")
async def health():
    gpu = bool(torch and torch.cuda.is_available())
    return {
        "status": "ok",
        "env": settings.APP_ENV,
        "gpu": gpu,
        "asr_model": settings.ASR_MODEL,
        "asr_language": settings.ASR_LANGUAGE,
        "llm_model": settings.LLM_MODEL,
        "process_mode": settings.PROCESS_MODE,
        "diarization": settings.DIARIZATION,
        "fast_mode": settings.FAST_MODE,
        "models_cache": str(Path(settings.MODELS_CACHE_DIR).resolve()),
        "data_dir": str(Path(settings.DATA_DIR).resolve()),
    }


@app.post("/transcribe")
async def transcribe(
    request: Request,
    file: UploadFile = File(...),
    fast_mode: Optional[bool] = Form(None),
    language: Optional[str] = Form(None),
):
    logger.info(f"Начало транскрипции файла: {file.filename}")
    
    if not file:
        raise APIError(400, "validation_error", "File is required")

    # Validate ext and size preliminarily
    filename = file.filename or "input"
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    logger.info(f"Расширение файла: {ext}")
    
    if not is_supported_ext(ext):
        raise APIError(415, "unsupported_media_type", f"Unsupported format: .{ext}")

    # Create job
    job_id = str(uuid.uuid4())
    logger.info(f"Создание задачи: {job_id}")
    
    paths = ensure_job_dirs(job_id)
    input_path = paths["in_dir"] / f"input.{ext}"
    
    logger.info(f"Сохранение файла: {input_path}")
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Normalize audio
    work_wav = paths["work_dir"] / "normalized.wav"
    logger.info(f"Нормализация аудио: {work_wav}")
    
    try:
        normalize_audio(input_path, work_wav)
        duration = probe_duration_sec(work_wav)
        logger.info(f"Длительность аудио: {duration:.1f} секунд")
    except Exception as e:
        logger.error(f"Ошибка при обработке аудио: {str(e)}", exc_info=True)
        raise APIError(500, "audio_processing_error", f"Ошибка обработки аудио: {str(e)}")
    
    if duration > settings.MAX_AUDIO_MIN * 60:
        raise APIError(413, "duration_limit", f"Audio too long: {duration:.1f}s")

    # Persist initial status
    status_path = paths["work_dir"] / "status.json"
    write_json(status_path, {"job_id": job_id, "status": "queued", "progress": 0})

    # Effective overrides
    effective_fast = settings.FAST_MODE if fast_mode is None else bool(fast_mode)
    effective_lang = settings.ASR_LANGUAGE if not language else language

    payload = {
        "job_id": job_id,
        "input_path": str(input_path.resolve()),
        "fast_mode": effective_fast,
        "language": effective_lang,
    }

    if settings.PROCESS_MODE == "async":
        # Enqueue RQ job
        try:
            from rq import Queue
            from redis import Redis
            from apps.worker.worker import worker_entry

            redis = Redis.from_url(settings.REDIS_URL)
            q = Queue("meeting_summarizer", connection=redis)
            q.enqueue(worker_entry, payload, job_timeout=settings.RQ_JOB_TIMEOUT)
        except Exception as e:  # pragma: no cover
            raise APIError(500, "queue_error", f"Failed to enqueue: {e}")
        return {"job_id": job_id, "status": "queued"}
    else:
        try:
            run_pipeline(payload)
            write_json(status_path, {"job_id": job_id, "status": "done", "progress": 100})
        except APIError:
            raise
        except Exception as e:
            write_json(status_path, {"job_id": job_id, "status": "error", "error": str(e)})
            raise APIError(500, "processing_error", str(e))
        return {"job_id": job_id, "status": "done"}


@app.get("/status/{job_id}")
async def status(job_id: str):
    paths = job_paths(job_id)
    status_path = paths["work_dir"] / "status.json"
    if status_path.exists():
        return read_json(status_path)
    raise APIError(404, "not_found", "Job not found")


@app.get("/result/{job_id}")
async def result(job_id: str):
    paths = job_paths(job_id)
    out_dir = paths["out_dir"]
    transcript_p = out_dir / "transcript.json"
    summary_p = out_dir / "summary.json"
    if not transcript_p.exists() or not summary_p.exists():
        raise APIError(404, "not_found", "Result not available")
    t = read_json(transcript_p)
    s = read_json(summary_p)
    return {
        "job_id": t.get("job_id", job_id),
        "language": t.get("language"),
        "duration_sec": t.get("duration_sec"),
        "speakers": t.get("speakers", []),
        "metrics": t.get("metrics", {}),
        "transcript": t,
        "summary": s,
    }


@app.post("/summary/stream")
async def summary_stream(body: dict):
    job_id = body.get("job_id")
    if not job_id:
        raise APIError(400, "validation_error", "job_id required")
    paths = job_paths(job_id)
    out_dir = paths["out_dir"]
    transcript_p = out_dir / "transcript.json"
    summary_p = out_dir / "summary.json"
    if not transcript_p.exists() or not summary_p.exists():
        raise APIError(404, "not_found", "Result not available")

    transcript = read_json(transcript_p)
    base_summary = read_json(summary_p)

    from kits.kit_llm.openai_backend import stream_tldr

    def event_gen():
        # 1) context
        context = {
            "language": transcript.get("language"),
            "duration_sec": transcript.get("duration_sec"),
            "first_speakers": transcript.get("speakers", [])[:2],
            "action_items": base_summary.get("action_items", []),
            "decisions": base_summary.get("decisions", []),
            "risks": base_summary.get("risks", []),
        }
        yield {
            "event": "context",
            "data": context,
        }
        # 2) token stream
        for token in stream_tldr(transcript):
            yield {"event": "token", "data": {"t": token}}
        # 3) done
        yield {"event": "done", "data": {"finish_reason": "stop"}}

    return EventSourceResponse(event_gen())


@app.get("/export/{job_id}.md")
async def export_md(job_id: str):
    paths = job_paths(job_id)
    f = paths["out_dir"] / "minutes.md"
    if not f.exists():
        raise APIError(404, "not_found", "File not found")
    return PlainTextResponse(f.read_text(encoding="utf-8"), media_type="text/markdown")


@app.get("/export/{job_id}.json")
async def export_json(job_id: str):
    paths = job_paths(job_id)
    out = paths["out_dir"]
    transcript = out / "transcript.json"
    summary = out / "summary.json"
    if not transcript.exists() or not summary.exists():
        raise APIError(404, "not_found", "Files not found")
    merged = {
        "transcript": read_json(transcript),
        "summary": read_json(summary),
    }
    return JSONResponse(merged)


@app.get("/export/{job_id}.srt")
async def export_srt(job_id: str):
    paths = job_paths(job_id)
    f = paths["out_dir"] / "subs.srt"
    if not f.exists():
        raise APIError(404, "not_found", "File not found")
    return PlainTextResponse(f.read_text(encoding="utf-8"), media_type="application/x-subrip")


@app.get("/export/{job_id}.vtt")
async def export_vtt(job_id: str):
    paths = job_paths(job_id)
    f = paths["out_dir"] / "subs.vtt"
    if not f.exists():
        raise APIError(404, "not_found", "File not found")
    return PlainTextResponse(f.read_text(encoding="utf-8"), media_type="text/vtt")


@app.delete("/result/{job_id}")
async def delete_result(job_id: str):
    paths = job_paths(job_id)
    base = paths["job_dir"]
    if not base.exists():
        raise APIError(404, "not_found", "Job not found")
    # Safe delete under data dir only
    if not within_data_dir(base):
        raise APIError(400, "validation_error", "Path traversal detected")
    # Recursive delete
    import shutil

    shutil.rmtree(base)
    return {"deleted": True}


@app.get("/metrics")
async def metrics():
    data_dir = Path(settings.DATA_DIR) / "uploads"
    total = failed = 0
    durations = []
    avg_conf_tokens = []
    speech_rates = []
    if data_dir.exists():
        for job in data_dir.iterdir():
            status_path = job / "work" / "status.json"
            if status_path.exists():
                total += 1
                st = read_json(status_path)
                if st.get("status") == "error":
                    failed += 1
            t_json = job / "out" / "transcript.json"
            if t_json.exists():
                t = read_json(t_json)
                if t.get("duration_sec"):
                    durations.append(t["duration_sec"])  # not exactly processing time, placeholder
                m = t.get("metrics", {})
                if m.get("speech_rate_wpm"):
                    speech_rates.append(m["speech_rate_wpm"])
            s_json = job / "out" / "summary.json"
            if s_json.exists():
                s = read_json(s_json)
                if s.get("_tokens_used"):
                    avg_conf_tokens.append(s.get("_tokens_used"))
    def _avg(arr):
        return round(sum(arr)/len(arr), 2) if arr else 0
    return {
        "jobs_total": total,
        "jobs_failed": failed,
        "avg_processing_sec": _avg(durations),
        "avg_conf_tokens": _avg(avg_conf_tokens),
        "avg_speech_rate_wpm": _avg(speech_rates),
    }

