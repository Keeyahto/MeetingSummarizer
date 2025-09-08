from kits.kit_export.minutes import build_minutes_md


def test_build_minutes_md_contains_sections():
    transcript = {
        "segments": [
            {"start": 12.3, "end": 15.0, "speaker": "Speaker 1", "text": "Hello team"},
        ],
        "topics": [{"title": "Intro", "start": 0.0, "end": 20.0}],
    }
    summary = {
        "tldr": "Short summary.",
        "decisions": ["Ship feature A"],
        "action_items": [{"text": "Do X", "owner": "Alex", "due": "2025-09-10"}],
        "risks": ["Risk Y"],
    }
    md = build_minutes_md(transcript, summary)
    assert "## TL;DR" in md
    assert "Short summary." in md
    assert "## Decisions" in md and "Ship feature A" in md
    assert "## Action Items" in md and "Do X" in md
    assert "## Risks" in md and "Risk Y" in md
    assert "## Transcript (speakers)" in md

