from kits.kit_export.subtitles import words_to_caption_lines, build_srt, build_vtt


def test_words_to_caption_lines_basic():
    words = [
        {"start": 0.0, "end": 0.4, "text": "Hello"},
        {"start": 0.5, "end": 1.0, "text": "world"},
    ]
    lines = words_to_caption_lines(words, max_chars=20)
    assert len(lines) == 1
    assert lines[0]["text"] == "Hello world"
    assert lines[0]["start"] == 0.0
    assert lines[0]["end"] == 1.0


def test_build_srt_and_vtt():
    words = [
        {"start": 0.0, "end": 1.0, "text": "Hello"},
        {"start": 1.0, "end": 2.0, "text": "world"},
    ]
    srt = build_srt(words)
    vtt = build_vtt(words)
    # words_to_caption_lines объединяет слова, поэтому время от начала первого до конца последнего
    assert "00:00:00,000 --> 00:00:02,000" in srt
    assert "00:00:00.000 --> 00:00:02.000" in vtt
    assert "Hello" in srt and "world" in srt
    assert vtt.startswith("WEBVTT")

