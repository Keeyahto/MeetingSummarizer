import json
from pathlib import Path


def test_pipeline_with_mocks(tmp_path, monkeypatch):
    # Point DATA_DIR to tmp
    monkeypatch.setattr("kits.kit_common.config.settings.DATA_DIR", str(tmp_path))

    # Mock ASR to return synthetic aligned segments with words
    from kits.kit_asr import whisperx_asr as asr

    def fake_asr(wav_path, language=None):
        return {
            "language": "en",
            "segments": [
                {
                    "start": 0.0,
                    "end": 1.0,
                    "text": "Hello world",
                    "speaker": "Speaker 1",
                    "words": [
                        {"start": 0.0, "end": 0.5, "text": "Hello", "speaker": "Speaker 1"},
                        {"start": 0.5, "end": 1.0, "text": "world", "speaker": "Speaker 1"},
                    ],
                }
            ],
        }

    monkeypatch.setattr(asr, "transcribe_with_whisperx", fake_asr)

    # Mock summarize to return deterministic response
    from kits.kit_llm import openai_backend as llm
    monkeypatch.setattr(
        llm,
        "summarize_transcript",
        lambda transcript: {
            "tldr": "Short summary.",
            "action_items": [{"text": "Do X", "owner": None, "due": None}],
            "decisions": ["Decide Y"],
            "risks": ["Risk Z"],
            "_tokens_used": 10,
        },
    )

    # Prepare job paths and a dummy normalized wav
    from kits.kit_common.paths import ensure_job_dirs
    job_id = "job-123"
    paths = ensure_job_dirs(job_id)
    work_wav = paths["work_dir"] / "normalized.wav"
    work_wav.write_bytes(b"RIFF")

    # Pretend duration is small
    from kits.utils import audio as audio_utils
    monkeypatch.setattr(audio_utils, "probe_duration_sec", lambda p: 5.0)

    # Run pipeline
    from kits.kit_pipeline.pipeline import run_pipeline
    res = run_pipeline({"job_id": job_id, "input_path": str(paths["in_dir"] / "input.wav"), "fast_mode": False, "language": "en"})

    out_dir = paths["out_dir"]
    # Validate files
    assert (out_dir / "transcript.json").exists()
    assert (out_dir / "summary.json").exists()
    assert (out_dir / "subs.srt").exists()
    assert (out_dir / "subs.vtt").exists()
    assert (out_dir / "minutes.md").exists()
    assert (out_dir / "minutes.json").exists()

    # Validate content
    tr = json.loads((out_dir / "transcript.json").read_text(encoding="utf-8"))
    sm = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    assert tr["language"] == "en"
    assert tr["segments"] and tr["segments"][0]["text"].startswith("Hello")
    assert sm["tldr"].startswith("Short")
    assert res["job_id"] == job_id

