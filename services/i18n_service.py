"""
services/i18n_service.py
Модуль интернационализации и управления языками интерфейса WaterMetrics (RU / EN).
"""

from typing import Dict
from PySide6.QtCore import QSettings, QObject, Signal


class I18nManager(QObject):
    """Менеджер локализации интерфейса с поддержкой горячей смены языка."""
    language_changed = Signal(str)

    TRANSLATIONS: Dict[str, Dict[str, str]] = {
        "ru": {
            # Приветственный экран (Welcome Wizard)
            "welcome_title": "Добро пожаловать в WaterMetrics!",
            "welcome_subtitle": "Профессиональная система автоматизированного расчета водопотребления",
            "welcome_step1_lang": "1. Выберите язык интерфейса / Select language:",
            "welcome_step2_theme": "2. Выберите стиль оформления (Live Preview):",
            "welcome_step3_waves": "3. Настройка фоновой графики:",
            "welcome_waves_enable": "🌊 Отображать живые 3D-волны заднего плана (OpenGL)",
            "welcome_waves_disable": "⚡ Минималистичный строгий режим (0% GPU)",
            "welcome_btn_start_tour": "✨ Применить и начать обучение первой проводке",
            "welcome_btn_skip": "Пропустить обучение и открыть дашборд",

            # Темы
            "theme_azure": "Dark Tech Azure (Лазурно-бирюзовый)",
            "theme_pearl": "Pearl Light (Жемчужно-светлый)",
            "theme_classic": "Как дома (Классический Аркус)",
            "theme_cyberpunk": "Cyberpunk Neon (Неоновый)",
            "theme_emerald": "Emerald Cyber (Изумрудный)",
            "theme_violet": "Deep Violet (Глубокий фиолетовый)",

            # Навигация
            "nav_dashboard": "Расчеты",
            "nav_norms": "Нормативы",
            "nav_logs": "Терминал логов",
            "nav_tests": "Авто-тесты",
            "nav_about": "О программе",

            # Обновления
            "upd_card_title": "Удаленные обновления ПО (GitHub Releases)",
            "upd_repo_label": "Репозиторий GitHub:",
            "upd_auto_check": "Автоматически проверять обновления при запуске",
            "upd_btn_check": "Проверить обновления",
            "upd_btn_check_now": "Проверить сейчас",
            "upd_status_idle": "Нажмите «Проверить сейчас», чтобы запросить последний релиз с GitHub.",
            "upd_status_checking": "Проверка обновлений в репозитории...",
            "upd_status_latest": "Установлена самая свежая версия",
            "upd_status_new": "Доступно обновление!",

            # Кнопки
            "btn_save": "Сохранить",
            "btn_apply": "Применить",
            "btn_cancel": "Отмена",
            "btn_close": "Закрыть",
            "btn_next": "Далее ›",
            "btn_prev": "‹ Назад",
            "btn_skip": "Пропустить"
        },
        "en": {
            # Welcome Wizard
            "welcome_title": "Welcome to WaterMetrics!",
            "welcome_subtitle": "Professional Automated Water Consumption & Billing System",
            "welcome_step1_lang": "1. Select interface language / Выберите язык:",
            "welcome_step2_theme": "2. Choose visual theme style (Live Preview):",
            "welcome_step3_waves": "3. Background graphics setup:",
            "welcome_waves_enable": "🌊 Enable dynamic 3D background waves (OpenGL)",
            "welcome_waves_disable": "⚡ Minimalist clean mode (0% GPU)",
            "welcome_btn_start_tour": "✨ Apply & start first billing onboarding",
            "welcome_btn_skip": "Skip tour and open dashboard",

            # Themes
            "theme_azure": "Dark Tech Azure (Azure Tech)",
            "theme_pearl": "Pearl Light (Clean White)",
            "theme_classic": "Arcus Classic (Windows Classic)",
            "theme_cyberpunk": "Cyberpunk Neon (Neon Pink)",
            "theme_emerald": "Emerald Cyber (Green Cyber)",
            "theme_violet": "Deep Violet (Purple Glass)",

            # Navigation
            "nav_dashboard": "Calculations",
            "nav_norms": "Standards",
            "nav_logs": "Log Terminal",
            "nav_tests": "Auto Tests",
            "nav_about": "About",

            # Updates
            "upd_card_title": "Remote Software Updates (GitHub Releases)",
            "upd_repo_label": "GitHub Repository:",
            "upd_auto_check": "Automatically check for updates on startup",
            "upd_btn_check": "Check for updates",
            "upd_btn_check_now": "Check now",
            "upd_status_idle": "Click «Check now» to query the latest release from GitHub.",
            "upd_status_checking": "Checking repository for updates...",
            "upd_status_latest": "You are using the latest version",
            "upd_status_new": "New update available!",

            # Buttons
            "btn_save": "Save",
            "btn_apply": "Apply",
            "btn_cancel": "Cancel",
            "btn_close": "Close",
            "btn_next": "Next ›",
            "btn_prev": "‹ Back",
            "btn_skip": "Skip"
        }
    }

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = I18nManager()
        return cls._instance

    def __init__(self):
        super().__init__()
        settings = QSettings("WaterMetrics", "Localization")
        self._current_lang = settings.value("Language", "ru", type=str)
        if self._current_lang not in self.TRANSLATIONS:
            self._current_lang = "ru"

    @property
    def current_language(self) -> str:
        return self._current_lang

    def set_language(self, lang_code: str):
        if lang_code in self.TRANSLATIONS and lang_code != self._current_lang:
            self._current_lang = lang_code
            QSettings("WaterMetrics", "Localization").setValue("Language", lang_code)
            self.language_changed.emit(lang_code)

    def t(self, key: str, default: str = "") -> str:
        """Получить перевод по ключу."""
        return self.TRANSLATIONS.get(self._current_lang, {}).get(key, default or key)


def tr(key: str, default: str = "") -> str:
    """Удобный хелпер для быстрого перевода."""
    return I18nManager.instance().t(key, default)
