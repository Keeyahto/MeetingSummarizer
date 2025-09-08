"""
Патч для WhisperX, чтобы он использовал наш метод поиска FFmpeg
"""
import subprocess
import shutil
from pathlib import Path


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


def patch_whisperx():
    """Применить патч к WhisperX"""
    try:
        import whisperx.audio
        
        # Сохраняем оригинальную функцию
        original_load_audio = whisperx.audio.load_audio
        
        def patched_load_audio(file: str, sr: int = 16000):
            """Патченная версия load_audio с правильным поиском FFmpeg"""
            import numpy as np
            
            try:
                # Находим FFmpeg
                ffmpeg_path = find_ffmpeg_binary("ffmpeg")
                
                # Launches a subprocess to decode audio while down-mixing and resampling as necessary.
                cmd = [
                    ffmpeg_path,
                    "-nostdin",
                    "-threads",
                    "0",
                    "-i",
                    file,
                    "-f",
                    "s16le",
                    "-ac",
                    "1",
                    "-acodec",
                    "pcm_s16le",
                    "-ar",
                    str(sr),
                    "-",
                ]
                out = subprocess.run(cmd, capture_output=True, check=True).stdout
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e

            return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0
        
        # Заменяем функцию
        whisperx.audio.load_audio = patched_load_audio
        print("WhisperX успешно заплачен для использования правильного FFmpeg")
        
    except ImportError:
        print("WhisperX не найден, патч не применен")
    except Exception as e:
        print(f"Ошибка при применении патча: {e}")


# Автоматически применяем патч при импорте
patch_whisperx()

