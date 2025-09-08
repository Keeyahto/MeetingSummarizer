"""
Точка входа для RQ worker
"""
from .worker import worker_entry

# Экспортируем функцию для RQ
__all__ = ['worker_entry']

