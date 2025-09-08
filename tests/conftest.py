import io
import os
from pathlib import Path
import json
import pytest


@pytest.fixture(scope="session")
def tmp_data_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("data")
    return d


@pytest.fixture(autouse=True)
def patch_settings(tmp_data_dir, monkeypatch):
    # Point DATA_DIR to temp and use sync mode for tests
    monkeypatch.setattr("kits.kit_common.config.settings.DATA_DIR", str(tmp_data_dir))
    monkeypatch.setattr("kits.kit_common.config.settings.PROCESS_MODE", "sync")
    # Ensure folders exist
    (Path(tmp_data_dir) / "uploads").mkdir(parents=True, exist_ok=True)


@pytest.fixture()
def test_app_client(monkeypatch):
    # Avoid ffmpeg and heavy compute in API paths
    from kits.utils import audio as audio_utils
    monkeypatch.setattr(audio_utils, "normalize_audio", lambda src, dst: Path(dst).write_bytes(b"RIFF"))
    monkeypatch.setattr(audio_utils, "probe_duration_sec", lambda p: 5.0)

    # Patch run_pipeline to write minimal outputs
    from kits.kit_pipeline import pipeline as pipe

    def fake_run(payload: dict):
        from kits.kit_common.paths import ensure_job_dirs
        paths = ensure_job_dirs(payload["job_id"])
        out = paths["out_dir"]
        out.mkdir(parents=True, exist_ok=True)
        transcript = {
            "job_id": payload["job_id"],
            "language": "en",
            "duration_sec": 5.0,
            "speakers": ["Speaker 1"],
            "metrics": {"speech_rate_wpm": 120, "talk_time": {"Speaker 1": 1.0}},
            "segments": [
                {"start": 0.0, "end": 1.0, "speaker": "Speaker 1", "text": "Hello world", "words": [
                    {"start": 0.0, "end": 0.5, "text": "Hello", "speaker": "Speaker 1"},
                    {"start": 0.5, "end": 1.0, "text": "world", "speaker": "Speaker 1"}
                ]}
            ],
            "keywords": ["hello", "world"],
            "topics": []
        }
        summary = {
            "tldr": "Short summary.",
            "action_items": [{"text": "Do X", "owner": None, "due": None}],
            "decisions": ["Decide Y"],
            "risks": ["Risk Z"],
            "_tokens_used": 12,
        }
        (out / "transcript.json").write_text(json.dumps(transcript), encoding="utf-8")
        (out / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
        (out / "subs.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nHello world\n", encoding="utf-8")
        (out / "subs.vtt").write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHello world\n\n", encoding="utf-8")
        (out / "minutes.md").write_text("# Meeting Minutes\n", encoding="utf-8")
        (out / "minutes.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
        return {"job_id": payload["job_id"], "status": "done"}

    monkeypatch.setattr(pipe, "run_pipeline", fake_run)

    # Patch SSE token generator to avoid contacting LLM
    from kits.kit_llm import openai_backend as llm
    monkeypatch.setattr(llm, "stream_tldr", lambda transcript: iter(["Short ", "summary."]))

    from fastapi.testclient import TestClient
    from apps.api.main import app
    client = TestClient(app)
    return client

