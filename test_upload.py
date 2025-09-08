import requests
import os

# Проверяем, что сервер запущен
try:
    response = requests.get("http://localhost:8000/health")
    print(f"Health check: {response.status_code}")
    if response.status_code == 200:
        print("Сервер работает!")
    else:
        print("Сервер не отвечает")
        exit(1)
except Exception as e:
    print(f"Ошибка подключения к серверу: {e}")
    exit(1)

# Тестируем загрузку файла
if os.path.exists("test.wav"):
    print("Тестовый файл найден, загружаем...")
    try:
        with open("test.wav", "rb") as f:
            files = {"file": ("test.wav", f, "audio/wav")}
            data = {"fast_mode": "true"}
            response = requests.post("http://localhost:8000/transcribe", files=files, data=data)
            print(f"Статус ответа: {response.status_code}")
            print(f"Ответ: {response.text}")
    except Exception as e:
        print(f"Ошибка при загрузке файла: {e}")
else:
    print("Тестовый файл test.wav не найден")

