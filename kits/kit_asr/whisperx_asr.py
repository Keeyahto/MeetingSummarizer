from typing import Dict, List
from pathlib import Path
from kits.kit_common.config import settings

# Применяем патч для WhisperX
from .whisperx_patch import patch_whisperx
patch_whisperx()


def transcribe_with_whisperx(wav_path: Path, language: str | None = None) -> Dict:
    import torch  # type: ignore
    import whisperx  # type: ignore
    import logging
    
    logger = logging.getLogger(__name__)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    audio_file = str(wav_path)
    batch_size = settings.ASR_BATCH_SIZE
    compute_type = settings.ASR_COMPUTE
    
    logger.info(f"WhisperX: устройство={device}, модель={settings.ASR_MODEL}, batch_size={batch_size}")
    logger.info(f"WhisperX: аудио файл={audio_file}")
    
    # 1. Transcribe with original whisper (batched) - согласно документации
    logger.info("Загрузка модели WhisperX...")
    model = whisperx.load_model(settings.ASR_MODEL, device, compute_type=compute_type)
    logger.info("Загрузка аудио...")
    audio = whisperx.load_audio(audio_file)
    logger.info("Начало транскрипции...")
    result = model.transcribe(audio, batch_size=batch_size)
    logger.info("Транскрипция завершена")
    
    # 2. Align whisper output - согласно документации
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
    
    # 3. Assign speaker labels - согласно документации
    if settings.DIARIZATION == "on" and settings.HF_TOKEN:
        try:
            diarize_model = whisperx.diarize.DiarizationPipeline(use_auth_token=settings.HF_TOKEN, device=device)
            diarize_segments = diarize_model(audio)
            result = whisperx.assign_word_speakers(diarize_segments, result)
        except Exception:
            # fall back silently
            pass

    return {"segments": result["segments"], "language": result.get("language")}


def pseudo_diarize(segments: List[Dict]) -> List[Dict]:
    # If no diarization info, alternate speakers on pauses > 0.5s
    out = []
    speaker_id = 1
    prev_end = 0.0
    for seg in segments:
        start = float(seg.get("start", 0))
        end = float(seg.get("end", start))
        if start - prev_end > 0.5:
            speaker_id = 2 if speaker_id == 1 else 1
        spk = f"Участник {speaker_id}"
        words = seg.get("words") or []
        for w in words:
            w["speaker"] = w.get("speaker") or spk
        out.append({
            "start": start,
            "end": end,
            "text": seg.get("text", ""),
            "speaker": seg.get("speaker") or spk,
            "words": words,
        })
        prev_end = end
    return out

