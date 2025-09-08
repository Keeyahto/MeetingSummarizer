# Meeting Summarizer — demo

_Читать на русском: [README.ru.md](./README.ru.md)_

A compact end‑to‑end demo of a meeting summarization service: upload audio, get accurate transcript with word‑level timestamps, a concise TL;DR, action items (with optional owner and due), decisions and risks, plus exports and a live TL;DR stream in the UI.

This repository is designed to showcase engineering approach, architecture, and implementation quality on a realistic problem.

## Highlights

- WhisperX speech recognition with word‑level alignment (drives SRT/VTT).
- Pseudo‑diarization out of the box; optional diarization via pyannote (with HF token).
- Structured summary via any OpenAI‑compatible LLM endpoint (e.g., LM Studio) returning strict JSON.
- Exports: Markdown minutes, combined JSON (transcript+summary), SRT and VTT.
- Live TL;DR over SSE for a smooth streaming UX.
- Conversation metrics: speech rate (wpm), talk‑time share by speaker, pause count, basic keywords.

## Where it fits

- Business meetings and project calls: decisions, follow‑ups, risks captured uniformly.
- Sales and support: call reviews with actionable items and risk highlights.
- Interviews and research: quick notes and subtitles; searchable transcript.
- Podcasts/lectures: timed navigation, minutes, captions.

## Architecture Overview

- Backend: FastAPI API with clean error model and CORS; sync or async processing with Redis + RQ worker.
- ASR: WhisperX (GPU/CPU), FFmpeg‑based audio normalization, safe cross‑platform paths.
- LLM: OpenAI‑compatible API with JSON‑schema responses and token‑streaming TL;DR.
- Frontend: Next.js 14 + Tailwind + Zustand; upload, status polling, results tabs, downloads, SSE TL;DR.
- Modules: `kits/kit_asr`, `kits/kit_llm`, `kits/kit_pipeline`, `kits/kit_export`, `kits/kit_common`, `apps/api`, `apps/worker`, `apps/web`.
- Docker Compose: services for API/worker/redis; volumes for data and models.
- Tests: pytest for API/pipeline/exports and Vitest for UI utils; heavy parts are mocked for speed.

## Produced Artifacts

- `transcript.json` — paragraphs with speaker, timestamps, words.
- `summary.json` — TL;DR, action items, decisions, risks (strict schema).
- `minutes.md` and `minutes.json` — human‑readable minutes + combined data.
- `subs.srt` and `subs.vtt` — captions built from aligned words.

## API Surface (for integration)

- `GET /health`
- `POST /transcribe` (multipart upload) → returns `job_id`
- `GET /status/{job_id}`
- `GET /result/{job_id}` — transcript, summary, metrics
- `POST /summary/stream` — SSE TL;DR token stream
- `GET /export/{job_id}.(md|json|srt|vtt)`
- `DELETE /result/{job_id}`
- `GET /metrics`

## Demo UI

- Upload area with drag‑and‑drop and format checks.
- Job progress with polling; automatic switch to results.
- Tabs: Overview (TL;DR, actions, decisions, risks), Transcript (search + speaker filter), Subtitles, Topics.
- Download buttons for `.md`, `.json`, `.srt`, `.vtt`; SSE button for live TL;DR.

## Why this matters for clients

- Adaptable: schema can be extended (e.g., blockers, dependencies), language/domain prompts adjusted, token budgets tuned.
- Private by design: can run fully local (ASR + LLM) or route selectively; no mandatory cloud uploads.
- Integration‑ready: REST + SSE, standard export formats, modular codebase, containerized setup.
- Quality‑minded: deterministic tests with mocks, clear error paths, logging and basic metrics.

For a detailed description in Russian (use‑cases, architecture, tests, and options), see [README.ru.md](README.ru.md).
