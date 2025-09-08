@echo off
set PATH=%PATH%;C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0-essentials_build\bin
call .venv\Scripts\activate
python -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload

