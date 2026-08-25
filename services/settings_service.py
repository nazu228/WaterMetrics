"""
Сервис персистентного управления настройками и нормативами WaterMetrics.
Поддерживает двухуровневое сохранение:
1. QSettings (реестр / системное хранилище ОС)
2. JSON-файл (~/.watermetrics/settings.json) для автономных скриптов и резервирования.
"""
import os
import json
from typing import Tuple, Any
from PySide6.QtCore import QSettings
import config

SETTINGS_FILE = os.path.join(config.DATA_DIR, "settings.json")


class SettingsService:
    """Централизованный сервис настроек и нормативов потребления."""

    HARDCODED_DEFAULT_COLD: float = 4.04
    HARDCODED_DEFAULT_HOT: float = 2.65

    @classmethod
    def _ensure_data_dir(cls):
        try:
            os.makedirs(config.DATA_DIR, exist_ok=True)
        except Exception:
            pass

    @classmethod
    def _read_json_settings(cls) -> dict:
        cls._ensure_data_dir()
        if not os.path.exists(SETTINGS_FILE):
            return {}
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @classmethod
    def _write_json_settings(cls, data: dict):
        cls._ensure_data_dir()
        try:
            current = cls._read_json_settings()
            current.update(data)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(current, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    @classmethod
    def get_norm_cold(cls) -> float:
        """Возвращает сохраненный норматив ХВС (м³/чел)."""
        try:
            q_settings = QSettings("WaterMetrics", "Norms")
            val = q_settings.value("NormCold", None)
            if val is not None:
                float_val = float(str(val).replace(",", "."))
                if float_val > 0:
                    return round(float_val, 3)
        except Exception:
            pass

        # Fallback к JSON
        json_data = cls._read_json_settings()
        if "norm_cold" in json_data:
            try:
                float_val = float(str(json_data["norm_cold"]).replace(",", "."))
                if float_val > 0:
                    return round(float_val, 3)
            except Exception:
                pass

        return getattr(config, "DEFAULT_NORM_COLD", cls.HARDCODED_DEFAULT_COLD)

    @classmethod
    def get_norm_hot(cls) -> float:
        """Возвращает сохраненный норматив ГВС (м³/чел)."""
        try:
            q_settings = QSettings("WaterMetrics", "Norms")
            val = q_settings.value("NormHot", None)
            if val is not None:
                float_val = float(str(val).replace(",", "."))
                if float_val > 0:
                    return round(float_val, 3)
        except Exception:
            pass

        # Fallback к JSON
        json_data = cls._read_json_settings()
        if "norm_hot" in json_data:
            try:
                float_val = float(str(json_data["norm_hot"]).replace(",", "."))
                if float_val > 0:
                    return round(float_val, 3)
            except Exception:
                pass

        return getattr(config, "DEFAULT_NORM_HOT", cls.HARDCODED_DEFAULT_HOT)

    @classmethod
    def get_norms(cls) -> Tuple[float, float]:
        """Возвращает кортеж (norm_cold, norm_hot)."""
        return cls.get_norm_cold(), cls.get_norm_hot()

    @classmethod
    def save_norms(cls, norm_cold: float, norm_hot: float) -> bool:
        """
        Сохраняет новые нормативы в QSettings, JSON и синхронизирует config.
        Возвращает True при успешном сохранении.
        """
        try:
            c_val = round(float(str(norm_cold).replace(",", ".")), 3)
            h_val = round(float(str(norm_hot).replace(",", ".")), 3)
            if c_val <= 0 or h_val <= 0:
                return False

            # 1. QSettings
            q_settings = QSettings("WaterMetrics", "Norms")
            q_settings.setValue("NormCold", c_val)
            q_settings.setValue("NormHot", h_val)
            q_settings.sync()

            # 2. JSON
            cls._write_json_settings({
                "norm_cold": c_val,
                "norm_hot": h_val
            })

            # 3. Синхронизация в глобальном config в памяти
            config.DEFAULT_NORM_COLD = c_val
            config.DEFAULT_NORM_HOT = h_val

            return True
        except Exception:
            return False

    @classmethod
    def reset_norms_to_default(cls) -> Tuple[float, float]:
        """Сбрасывает нормативы к заводским значениям (4.04, 2.65)."""
        cls.save_norms(cls.HARDCODED_DEFAULT_COLD, cls.HARDCODED_DEFAULT_HOT)
        return cls.HARDCODED_DEFAULT_COLD, cls.HARDCODED_DEFAULT_HOT
