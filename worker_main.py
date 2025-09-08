#!/usr/bin/env python3
"""
Простой worker для MeetingSummarizer
"""
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from redis import Redis
from rq import Worker
from kits.kit_common.config import settings

# Импортируем функцию worker_entry
from apps.worker.worker import worker_entry

def main():
    print("Запуск MeetingSummarizer Worker...")
    print(f"Redis URL: {settings.REDIS_URL}")
    
    # Подключение к Redis
    redis_conn = Redis.from_url(settings.REDIS_URL)
    
    # Создание worker
    worker = Worker(['meeting_summarizer'], connection=redis_conn)
    
    print("Worker запущен. Ожидание задач...")
    print("Нажмите Ctrl+C для остановки")
    
    try:
        worker.work()
    except KeyboardInterrupt:
        print("\nОстановка worker...")

if __name__ == "__main__":
    main()

