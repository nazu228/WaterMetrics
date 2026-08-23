"""
ui/dialogs/welcome_dialog.py
Модальное окно первичной настройки (Welcome Setup Wizard) с живым предпросмотром (Live Preview).
Позволяет пользователю выбрать язык, тему оформления и режим 3D-волн с мгновенной реакцией интерфейса.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QRadioButton, QButtonGroup, QFrame, QApplication, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QSettings, Signal
from PySide6.QtGui import QColor, QFont

from ui.styles import ThemeManager, get_svg_icon
from ui.components.interactive import HoverGlassCard
from ui.components.glass_icon import GlassIconWidget
from services.i18n_service import I18nManager, tr
from config import APP_VERSION


class ThemePreviewCard(QFrame):
    """Интерактивная карточка выбора темы с цветовой палитрой."""

    def __init__(self, theme_name: str, display_label: str, colors: list, is_active: bool = False, on_select=None, parent=None):
        super().__init__(parent)
        self.setObjectName("ThemePreviewCard")
        self.theme_name = theme_name
        self.on_select = on_select
        self.is_active = is_active
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(48)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.init_ui(display_label, colors)
        self.update_style()

    def init_ui(self, display_label: str, colors: list):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(10)

        # Кружочки палитры
        palette_lay = QHBoxLayout()
        palette_lay.setSpacing(4)
        for col in colors[:3]:
            dot = QLabel()
            dot.setFixedSize(14, 14)
            dot.setStyleSheet(f"background-color: {col}; border-radius: 7px; border: 1px solid rgba(255, 255, 255, 0.4);")
            palette_lay.addWidget(dot)
        lay.addLayout(palette_lay)

        self.lbl_name = QLabel(display_label)
        self.lbl_name.setStyleSheet("font-size: 12px; font-weight: 600; background: transparent; border: none;")
        lay.addWidget(self.lbl_name, 1)

        self.lbl_check = QLabel("✓" if self.is_active else "")
        self.lbl_check.setStyleSheet("font-size: 14px; font-weight: bold; color: #00F2FE; background: transparent; border: none;")
        lay.addWidget(self.lbl_check)

    def set_active(self, active: bool):
        self.is_active = active
        self.lbl_check.setText("✓" if active else "")
        self.update_style()

    def update_style(self):
        accent = ThemeManager.get_current_accent_color()
        if self.is_active:
            self.setStyleSheet(f"""
                QFrame#ThemePreviewCard {{
                    background: rgba(0, 242, 254, 0.16);
                    border: 1.5px solid {accent};
                    border-radius: 10px;
                }}
            """)
        else:
            self.setStyleSheet("""
                QFrame#ThemePreviewCard {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 10px;
                }
                QFrame#ThemePreviewCard:hover {
                    background: rgba(255, 255, 255, 0.10);
                    border: 1px solid rgba(255, 255, 255, 0.25);
                }
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.on_select:
            self.on_select(self.theme_name)
        super().mousePressEvent(event)


class WelcomeSetupDialog(QDialog):
    """
    Мастер первого запуска с мгновенным Live-предпросмотром тем оформления и 3D-волн.
    """

    def __init__(self, main_win=None, parent=None):
        super().__init__(parent or main_win)
        self.main_win = main_win
        self.start_onboarding_requested = False

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(740, 600)

        self.theme_cards = []
        self.init_ui()

    def init_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)

        curr_theme = ThemeManager.get_current_theme_name()
        accent = ThemeManager.get_current_accent_color()
        is_light = curr_theme in ("Pearl Light", "Как дома")

        self.card = HoverGlassCard(self)
        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(14)

        # ─── 1. Заголовок и Бренд ───
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        self.glass_icon = GlassIconWidget("droplet", accent, size=QSize(42, 42))
        header_row.addWidget(self.glass_icon)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)

        self.lbl_title = QLabel(tr("welcome_title", "Добро пожаловать в WaterMetrics!"))
        title_col = "#0A246A" if curr_theme == "Как дома" else ("#0F172A" if is_light else "#F8FAFC")
        self.lbl_title.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {title_col};")

        self.lbl_subtitle = QLabel(f"WaterMetrics v{APP_VERSION} — {tr('welcome_subtitle', 'Первичная настройка системы')}")
        self.lbl_subtitle.setStyleSheet("font-size: 12px; color: #94A3B8;")
        title_vbox.addWidget(self.lbl_title)
        title_vbox.addWidget(self.lbl_subtitle)

        header_row.addLayout(title_vbox, 1)

        # Бейдж версии
        ver_badge = QLabel(f"v{APP_VERSION}")
        ver_badge.setStyleSheet(f"background: rgba(0, 242, 254, 0.15); color: {accent}; font-size: 11px; font-weight: bold; padding: 4px 8px; border-radius: 6px;")
        header_row.addWidget(ver_badge)

        layout.addLayout(header_row)

        # ─── 2. Выбор языка ───
        self.lbl_lang_section = QLabel(tr("welcome_step1_lang", "1. Язык интерфейса / Interface language:"))
        self.lbl_lang_section.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {accent}; margin-top: 4px;")
        layout.addWidget(self.lbl_lang_section)

        lang_box = QHBoxLayout()
        lang_box.setSpacing(10)

        curr_lang = I18nManager.instance().current_language

        self.btn_lang_ru = QPushButton("🇷🇺 Русский")
        self.btn_lang_ru.setCheckable(True)
        self.btn_lang_ru.setChecked(curr_lang == "ru")
        self.btn_lang_ru.setMinimumHeight(34)
        self.btn_lang_ru.clicked.connect(lambda: self._set_language("ru"))

        self.btn_lang_en = QPushButton("🇬🇧 English")
        self.btn_lang_en.setCheckable(True)
        self.btn_lang_en.setChecked(curr_lang == "en")
        self.btn_lang_en.setMinimumHeight(34)
        self.btn_lang_en.clicked.connect(lambda: self._set_language("en"))

        lang_box.addWidget(self.btn_lang_ru)
        lang_box.addWidget(self.btn_lang_en)
        lang_box.addStretch()
        layout.addLayout(lang_box)

        # ─── 3. Выбор стиля оформления (Live Preview) ───
        self.lbl_theme_section = QLabel(tr("welcome_step2_theme", "2. Выберите стиль оформления (Live Preview):"))
        self.lbl_theme_section.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {accent}; margin-top: 4px;")
        layout.addWidget(self.lbl_theme_section)

        grid_themes = QGridLayout()
        grid_themes.setSpacing(8)

        themes_data = [
            ("Dark Tech Azure", "Dark Tech Azure", ["#00F2FE", "#028090", "#030712"]),
            ("Pearl Light", "Pearl Light", ["#028090", "#00A896", "#F1F5F9"]),
            ("Как дома", "Как дома (Arcus Classic)", ["#0A246A", "#7F9DB9", "#ECE9D8"]),
            ("Cyberpunk Neon", "Cyberpunk Neon", ["#FF007F", "#D9006C", "#05000A"]),
            ("Emerald Cyber", "Emerald Cyber", ["#10B981", "#064E3B", "#02120C"]),
            ("Deep Violet Glass", "Deep Violet Glass", ["#A855F7", "#4C1D95", "#090514"])
        ]

        self.theme_cards = []
        for idx, (tname, dname, cols) in enumerate(themes_data):
            is_active = (tname == curr_theme)
            card = ThemePreviewCard(tname, dname, cols, is_active=is_active, on_select=self._on_theme_selected)
            self.theme_cards.append(card)
            r = idx // 2
            c = idx % 2
            grid_themes.addWidget(card, r, c)

        layout.addLayout(grid_themes)

        # ─── 4. Настройка 3D-волн заднего плана (Live Preview) ───
        self.lbl_waves_section = QLabel(tr("welcome_step3_waves", "3. Настройка фоновой 3D-графики (OpenGL):"))
        self.lbl_waves_section.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {accent}; margin-top: 4px;")
        layout.addWidget(self.lbl_waves_section)

        wave_settings = QSettings("WaterMetrics", "WaveSettings")
        waves_enabled = wave_settings.value("WavesEnabled", True, type=bool)

        waves_box = QHBoxLayout()
        waves_box.setSpacing(10)

        self.btn_wave_on = QPushButton(tr("welcome_waves_enable", "🌊 Живые 3D-волны"))
        self.btn_wave_on.setCheckable(True)
        self.btn_wave_on.setChecked(waves_enabled)
        self.btn_wave_on.setMinimumHeight(34)
        self.btn_wave_on.clicked.connect(lambda: self._set_waves_enabled(True))

        self.btn_wave_off = QPushButton(tr("welcome_waves_disable", "⚡ Строгий 0% GPU"))
        self.btn_wave_off.setCheckable(True)
        self.btn_wave_off.setChecked(not waves_enabled)
        self.btn_wave_off.setMinimumHeight(34)
        self.btn_wave_off.clicked.connect(lambda: self._set_waves_enabled(False))

        waves_box.addWidget(self.btn_wave_on)
        waves_box.addWidget(self.btn_wave_off)
        waves_box.addStretch()
        layout.addLayout(waves_box)

        # ─── 5. Кнопки завершения мастера ───
        btn_action_box = QHBoxLayout()
        btn_action_box.setSpacing(10)

        self.btn_skip = QPushButton(tr("welcome_btn_skip", "Пропустить обучение"), objectName="SecondaryButton")
        self.btn_skip.setMinimumHeight(38)
        self.btn_skip.clicked.connect(self._on_skip_clicked)

        self.btn_start = QPushButton(tr("welcome_btn_start_tour", "✨ Начать обучение проводке"), objectName="PrimaryButton")
        self.btn_start.setIcon(get_svg_icon("sparkles", color="#020617" if not is_light else "#FFFFFF"))
        self.btn_start.setMinimumHeight(38)
        self.btn_start.clicked.connect(self._on_start_clicked)

        btn_action_box.addWidget(self.btn_skip)
        btn_action_box.addStretch()
        btn_action_box.addWidget(self.btn_start)

        layout.addLayout(btn_action_box)
        root_lay.addWidget(self.card)

    def _set_language(self, lang_code: str):
        I18nManager.instance().set_language(lang_code)
        self.btn_lang_ru.setChecked(lang_code == "ru")
        self.btn_lang_en.setChecked(lang_code == "en")
        self._refresh_texts()

    def _refresh_texts(self):
        self.lbl_title.setText(tr("welcome_title", "Добро пожаловать в WaterMetrics!"))
        self.lbl_subtitle.setText(f"WaterMetrics v{APP_VERSION} — {tr('welcome_subtitle', 'Первичная настройка системы')}")
        self.lbl_lang_section.setText(tr("welcome_step1_lang", "1. Язык интерфейса / Interface language:"))
        self.lbl_theme_section.setText(tr("welcome_step2_theme", "2. Выберите стиль оформления (Live Preview):"))
        self.lbl_waves_section.setText(tr("welcome_step3_waves", "3. Настройка фоновой 3D-графики (OpenGL):"))
        self.btn_wave_on.setText(tr("welcome_waves_enable", "🌊 Живые 3D-волны"))
        self.btn_wave_off.setText(tr("welcome_waves_disable", "⚡ Строгий 0% GPU"))
        self.btn_skip.setText(tr("welcome_btn_skip", "Пропустить обучение"))
        self.btn_start.setText(tr("welcome_btn_start_tour", "✨ Начать обучение первой проводке"))

    def _on_theme_selected(self, theme_name: str):
        for c in self.theme_cards:
            c.set_active(c.theme_name == theme_name)

        # Мгновенно применяем тему для Live-предпросмотра в фоне!
        ThemeManager.apply_theme(theme_name)

        # Обновляем цвета внутри диалога
        accent = ThemeManager.get_current_accent_color()
        if hasattr(self, 'glass_icon'):
            self.glass_icon.set_color(accent)

        if self.main_win and hasattr(self.main_win, 'ocean_bg'):
            self.main_win.ocean_bg.update()
        if self.main_win:
            self.main_win.update()

    def _set_waves_enabled(self, enabled: bool):
        self.btn_wave_on.setChecked(enabled)
        self.btn_wave_off.setChecked(not enabled)

        QSettings("WaterMetrics", "WaveSettings").setValue("WavesEnabled", enabled)
        if self.main_win and hasattr(self.main_win, 'ocean_bg'):
            if hasattr(self.main_win.ocean_bg, 'set_waves_enabled'):
                self.main_win.ocean_bg.set_waves_enabled(enabled)
            self.main_win.ocean_bg.update()

    def _on_start_clicked(self):
        self._save_setup_done()
        self.start_onboarding_requested = True
        self.accept()

    def _on_skip_clicked(self):
        self._save_setup_done()
        self.start_onboarding_requested = False
        self.reject()

    def _save_setup_done(self):
        settings = QSettings("WaterMetrics", "WelcomeSetup")
        settings.setValue("FirstRunSetupCompleted", True)
