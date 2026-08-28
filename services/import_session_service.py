"""
services/import_session_service.py — Сервис управления кэшем импортированных показаний в текущей сессии.

Хранит в оперативной памяти данные загруженной таблицы набивки (Теплосеть, Сводка и т.д.)
до закрытия приложения, позволяя автоматически предлагать показатели (ХВС, ГВС, ДОБ)
при переключении между домами.
"""
from typing import Dict, List, Optional, Tuple, Any
import os
import re

from core.excel_parser import ExcelManager


class ImportSessionService:
    """Кэш импортированных таблиц набивки в рамках сессии."""

    _active_file_path: str = ""
    _active_sheet_name: str = ""
    _rows_data: List[List[str]] = []
    _mapping: Dict[str, int] = {}
    _cached_house_values: Dict[str, Dict[str, float]] = {}

    @classmethod
    def set_session_import(
        cls,
        file_path: str,
        sheet_name: str,
        rows_data: List[List[str]],
        mapping: Dict[str, int]
    ) -> None:
        """Сохраняет загруженную таблицу и маппинг в кэш сессии."""
        cls._active_file_path = file_path
        cls._active_sheet_name = sheet_name
        cls._rows_data = rows_data
        cls._mapping = mapping
        cls._cached_house_values.clear()

        # Предварительное кэширование значений для всех строк с данными
        if rows_data and ('хвс' in mapping or 'гвс' in mapping):
            col_house = mapping.get('дом')
            col_hvs = mapping.get('хвс')
            col_gvs = mapping.get('гвс')
            col_dob = mapping.get('доб')

            for r_idx, row in enumerate(rows_data):
                val_hvs = ExcelManager.parse_float_safe(row[col_hvs]) if col_hvs is not None and col_hvs < len(row) else None
                val_gvs = ExcelManager.parse_float_safe(row[col_gvs]) if col_gvs is not None and col_gvs < len(row) else None
                val_dob = ExcelManager.parse_float_safe(row[col_dob]) if col_dob is not None and col_dob < len(row) else None

                if val_hvs is not None or val_gvs is not None or val_dob is not None:
                    # Ищем адрес дома в строке
                    house_text = ""
                    if col_house is not None and col_house < len(row) and row[col_house]:
                        house_text = str(row[col_house]).strip()
                    else:
                        for cell in row:
                            if cell and any(k in str(cell).lower() for k in ['цел', 'пос', 'душ', 'дуб', 'зел', 'авер', 'гасс', 'трош', 'дом', 'ул']):
                                house_text = str(cell).strip()
                                break

                    if house_text:
                        cls._cached_house_values[house_text] = {
                            'хвс': val_hvs if val_hvs is not None else 0.0,
                            'гвс': val_gvs if val_gvs is not None else 0.0,
                            'доб': val_dob if val_dob is not None else 0.0,
                            'row_idx': r_idx
                        }

    @classmethod
    def get_values_for_house(cls, house_name: str) -> Optional[Dict[str, float]]:
        """Ищет показатели ХВС, ГВС и ДОБ для дома в кэше сессии."""
        if not house_name:
            return None

        # 1. Быстрый поиск по кэшированным домам
        from services.folder_service import FolderNavigationService
        for cached_addr, vals in cls._cached_house_values.items():
            if FolderNavigationService.is_house_match(house_name, cached_addr):
                return vals

        # 2. Полный поиск по строкам, если маппинг активен
        if cls._rows_data and cls._mapping:
            res = ExcelManager.extract_values_by_mapping(cls._rows_data, cls._mapping, house_name)
            if res:
                cls._cached_house_values[house_name] = res
                return res

        return None

    @classmethod
    def has_active_session(cls) -> bool:
        """Проверяет, загружена ли таблица импорта в текущей сессии."""
        return bool(cls._rows_data and cls._mapping)

    @classmethod
    def get_active_info(cls) -> Dict[str, str]:
        """Возвращает информацию об активной таблице импорта."""
        return {
            'file_name': os.path.basename(cls._active_file_path) if cls._active_file_path else "",
            'file_path': cls._active_file_path,
            'sheet_name': cls._active_sheet_name,
            'houses_count': str(len(cls._cached_house_values))
        }

    @classmethod
    def clear_session(cls) -> None:
        """Очищает кэш текущей сессии."""
        cls._active_file_path = ""
        cls._active_sheet_name = ""
        cls._rows_data = []
        cls._mapping = {}
        cls._cached_house_values.clear()
