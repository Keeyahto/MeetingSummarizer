import subprocess
import shutil
from pathlib import Path

SUPPORTED_EXTS = {"mp3", "m4a", "aac", "wav", "ogg", "opus", "webm"}


def is_supported_ext(ext: str) -> bool:
    return ext.lower() in SUPPORTED_EXTS


def find_ffmpeg_binary(name: str) -> str:
    """Найти исполняемый файл FFmpeg в системе"""
    # Сначала попробуем найти в PATH
    binary = shutil.which(name)
    if binary:
        return binary
    
    # Если не найден, попробуем стандартные пути установки
    username = subprocess.os.environ.get('USERNAME', '')
    possible_paths = [
        f"C:\\Users\\{username}\\AppData\\Local\\Microsoft\\WinGet\\Packages\\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\\ffmpeg-8.0-essentials_build\\bin\\{name}.exe",
        f"C:\\ffmpeg\\bin\\{name}.exe",
        f"C:\\Program Files\\ffmpeg\\bin\\{name}.exe",
        f"C:\\Program Files (x86)\\ffmpeg\\bin\\{name}.exe",
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            return path
    
    raise RuntimeError(f"{name} не найден. Установите FFmpeg или добавьте его в PATH.")


def run_cmd(cmd: list[str]):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "Command failed")
    return proc.stdout


def normalize_audio(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_path = find_ffmpeg_binary("ffmpeg")
    cmd = [
        ffmpeg_path,
        "-y",
        "-i",
        str(src),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-acodec",
        "pcm_s16le",
        str(dst),
    ]
    run_cmd(cmd)


def probe_duration_sec(path: Path) -> float:
    ffprobe_path = find_ffmpeg_binary("ffprobe")
    cmd = [
        ffprobe_path,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    out = run_cmd(cmd)
    try:
        return float(out.strip())
    except Exception:
        return 0.0

