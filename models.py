"""
Модели данных предметной области WaterMetrics.
"""
from dataclasses import dataclass, field
from typing import List

@dataclass
class ClosedMeterRecord:
    """Запись о снятом (закрытом) счетчике."""
    apartment: str        # Например: "квартира 86"
    water_type: str       # 'cold' или 'hot'
    meter_num: int        # 1, 2 и т.д.
    final_reading: float  # Финальное показание снятия (Предыдущее = Текущее)

@dataclass
class NewMeterRecord:
    """Запись о новом счетчике (уходит в основную таблицу)."""
    apartment: str          # Например: "квартира 86"
    water_type: str         # 'cold' или 'hot'
    meter_num: int          # 1, 2 и т.д.
    initial_reading: float  # Стартовое показание (Предыдущее)

@dataclass
class CalculationConfig:
    """Конфигурация текущего расчета."""
    target_cold: float
    target_hot: float
    add_hvs: float
    norm_cold: float
    norm_hot: float
    template_path: str
    arcus_path: str
    save_path: str
    closed_meters: List[ClosedMeterRecord] = field(default_factory=list)
    new_meters: List[NewMeterRecord] = field(default_factory=list)