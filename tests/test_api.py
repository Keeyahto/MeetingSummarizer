import io
import json


def test_health(test_app_client):
    r = test_app_client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "process_mode" in data


def test_transcribe_sync_and_result(test_app_client, tmp_path):
    # Upload a tiny wav (content irrelevant; normalize_audio is patched)
    files = {"file": ("test.wav", b"RIFFDATA", "audio/wav")}
    r = test_app_client.post("/transcribe", files=files)
    assert r.status_code == 200
    job_id = r.json()["job_id"]

    # Status should eventually be done (our patched run writes immediately)
    st = test_app_client.get(f"/status/{job_id}")
    assert st.status_code == 200

    # Get result
    res = test_app_client.get(f"/result/{job_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["summary"]["tldr"].startswith("Short")


def test_exports_and_sse(test_app_client):
    # Similar to above: create a job by uploading
    files = {"file": ("test.wav", b"RIFFDATA", "audio/wav")}
    r = test_app_client.post("/transcribe", files=files)
    job_id = r.json()["job_id"]

    # Exports
    assert test_app_client.get(f"/export/{job_id}.md").status_code == 200
    assert test_app_client.get(f"/export/{job_id}.json").status_code == 200
    assert test_app_client.get(f"/export/{job_id}.srt").status_code == 200
    assert test_app_client.get(f"/export/{job_id}.vtt").status_code == 200

    # SSE stream: context, tokens, done
    with test_app_client.stream("POST", "/summary/stream", json={"job_id": job_id}) as resp:
        assert resp.status_code == 200
        content = "".join(list(resp.iter_text()))
        assert "event: context" in content
        assert "event: token" in content
        assert "event: done" in content

