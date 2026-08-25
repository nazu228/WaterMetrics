"""
Конфигурация приложения WaterMetrics.
Содержит настройки интерфейса, путей и стандартные нормативы.
"""
import os

# Базовые константы
DEFAULT_NORM_COLD: float = 4.04
DEFAULT_NORM_HOT: float = 2.65

# Пути
DATA_DIR: str = os.path.join(os.path.expanduser("~"), ".watermetrics")
HISTORY_FILE: str = os.path.join(DATA_DIR, "history.json")
BACKUP_DIR: str = os.path.join(DATA_DIR, "backups")

# Версия приложения
APP_VERSION: str = "1.0.22"

# Обновления через GitHub
DEFAULT_GITHUB_REPO: str = "nazu228/WaterMetrics"
GITHUB_API_BASE: str = "https://api.github.com/repos"

# Демонстрационные файлы для обучения (первой проводки)
DEMO_TEMPLATE_FILENAME: str = "Душистая 45+.xlsx"
DEMO_ARCUS_FILENAME: str = "душ 45 аркус.xlsx"

# Темы и цвета (Premium UI)
THEME = {
    "primary": "#00d890",
    "primary_hover": "#00e699",
    "danger": "#ff5555",
    "info": "#00d2ff",
    "bg_dark": "#1A1A1A",
    "bg_light": "#F0F0F0",
    "text_dark": "#FFFFFF",
    "text_light": "#000000"
}

# Инициализация директорий
os.makedirs(BACKUP_DIR, exist_ok=True)