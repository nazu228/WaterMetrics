"""Сервис персистентного управления историей файлов."""
import json
import os
from typing import List
from config import HISTORY_FILE


class HistoryService:
    @staticmethod
    def load() -> List[str]:
        """Загружает историю, отсеивая удаленные файлы."""
        if not os.path.exists(HISTORY_FILE):
            return []
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                paths = json.load(f)
            # Валидация существования файлов на диске
            valid_paths = [p for p in paths if isinstance(p, str) and os.path.isfile(p)]
            if len(valid_paths) != len(paths):
                HistoryService.save(valid_paths)
            return valid_paths
        except (json.JSONDecodeError, IOError):
            return []

    @staticmethod
    def save(paths: List[str]) -> None:
        """Сохраняет актуальный список путей."""
        try:
            os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(paths, f, ensure_ascii=False, indent=4)
        except IOError:
            pass

    @staticmethod
    def add_path(path: str) -> List[str]:
        """Добавляет новый путь в начало истории, удаляет дубликаты и сохраняет."""
        paths = HistoryService.load()
        norm_path = os.path.normpath(path)
        paths = [p for p in paths if os.path.normpath(p) != norm_path]
        paths.insert(0, norm_path)
        HistoryService.save(paths)
        return paths

    @staticmethod
    def clear() -> None:
        """Очищает историю отчетов."""
        HistoryService.save([])