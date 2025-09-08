#!/usr/bin/env python3
"""
Запуск worker для обработки задач из Redis очереди
"""
import os
import sys
from pathlib import Path
import platform

# Добавляем корневую директорию в PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from redis import Redis
from rq import Worker, SimpleWorker
from kits.kit_common.config import settings
from apps.worker.worker import worker_entry  # оставляем импорт, чтобы функции были загружены

def main():
    print("Запуск MeetingSummarizer Worker...")
    print(f"Redis URL: {settings.REDIS_URL}")

    # Подключение к Redis
    redis_conn = Redis.from_url(settings.REDIS_URL)

    # Для Windows используем SimpleWorker (без fork)
    is_windows = os.name == "nt" or platform.system().lower().startswith("win")
    worker_cls = SimpleWorker if is_windows else Worker

    # Создание worker для очереди 'meeting_summarizer'
    worker = worker_cls(['meeting_summarizer'], connection=redis_conn)

    print(f"Worker класс: {worker_cls.__name__}")
    print("Worker запущен. Ожидание задач...")
    print("Нажмите Ctrl+C для остановки")

    try:
        # Работает и для SimpleWorker, и для Worker
        worker.work(with_scheduler=True)
    except KeyboardInterrupt:
        print("\nОстановка worker...")
        try:
            worker.stop()
        except Exception:
            pass

if __name__ == "__main__":
    main()
