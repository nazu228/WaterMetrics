"""
ui/about_page.py — Экран "О программе" и Кастомизация 3D-волн и минимализма.
"""

import os
import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QDialog, QFrame, QApplication, QSlider, QCheckBox, QScrollArea, QLineEdit
)
from PySide6.QtCore import Qt, QSize, QSettings, Slot
from PySide6.QtGui import QMovie

from config import APP_VERSION, DEFAULT_GITHUB_REPO
from services.updater_service import GitHubUpdateChecker, GitHubReleaseInfo
from ui.dialogs.update_dialog import UpdateDialog
from ui.styles import get_svg_icon, ThemeManager
from ui.components.interactive import HoverGlassCard
from ui.components.toast import ToastNotification
from ui.components.glass_icon import GlassIconWidget


def get_asset_path(filename: str) -> str:
    """
    Универсальный поиск файлов ресурсов (assets).
    """
    candidates = []

    if hasattr(sys, '_MEIPASS'):
        candidates.append(os.path.join(sys._MEIPASS, "assets", filename))
        candidates.append(os.path.join(sys._MEIPASS, filename))

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    candidates.append(os.path.join(base_dir, "assets", filename))
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", filename))

    cwd = os.getcwd()
    candidates.append(os.path.join(cwd, "assets", filename))
    candidates.append(os.path.join(cwd, "pyside", "assets", filename))
    candidates.append(os.path.join(cwd, "pyside", filename))

    for path in candidates:
        norm_p = os.path.normpath(path)
        if os.path.isfile(norm_p):
            return norm_p

    return os.path.normpath(os.path.join(base_dir, "assets", filename))


class DonateDialog(QDialog):
    """Стильное бесшовное модальное окно пожертвований."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(460, 260)
        self.card_number = "40817810807004134433"
        self.init_ui()

    def init_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)

        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        accent = ThemeManager.get_current_accent_color()

        self.card = HoverGlassCard()
        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        lbl_title = QLabel("Поддержка разработки WaterMetrics", objectName="PageTitle")
        title_col = "#0A246A" if curr_theme == "Как дома" else ("#0F172A" if is_light else "#F8FAFC")
        lbl_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {title_col};")
        btn_x = QPushButton("✕")
        btn_x.setFixedSize(28, 28)
        btn_x.setCursor(Qt.PointingHandCursor)
        close_btn_bg = "rgba(0, 0, 0, 0.05)" if is_light else "rgba(255, 255, 255, 0.07)"
        close_btn_col = "#475569" if is_light else "#94A3B8"
        btn_x.setStyleSheet(f"QPushButton {{ background: {close_btn_bg}; color: {close_btn_col}; border: 1px solid rgba(0, 0, 0, 0.15); border-radius: 8px; font-size: 13px; font-weight: bold; }} QPushButton:hover {{ background: rgba(239, 68, 68, 0.45); color: #FFFFFF; }}")
        btn_x.clicked.connect(self.reject)

        header_row.addWidget(lbl_title, 1)
        header_row.addWidget(btn_x)
        layout.addLayout(header_row)

        card_frame = HoverGlassCard()
        card_lay = QVBoxLayout(card_frame)
        card_lay.setContentsMargins(16, 12, 16, 12)
        card_lay.setSpacing(6)

        lbl_bank = QLabel("Сбербанк / Номер счета / карты:")
        sub_col = "#475569" if is_light else "#94A3B8"
        lbl_bank.setStyleSheet(f"color: {sub_col}; font-size: 12px;")

        lbl_num = QLabel(self.card_number)
        num_col = ("#0A246A" if curr_theme == "Как дома" else "#028090") if is_light else accent
        lbl_num.setStyleSheet(f"""
            color: {num_col};
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 17px;
            font-weight: bold;
            letter-spacing: 1.5px;
            background: transparent;
        """)
        lbl_num.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        card_lay.addWidget(lbl_bank)
        card_lay.addWidget(lbl_num)
        layout.addWidget(card_frame)

        btn_box = QHBoxLayout()
        btn_copy = QPushButton("  Скопировать номер", objectName="PrimaryButton")
        copy_icon_col = "#FFFFFF" if is_light else "#020617"
        btn_copy.setIcon(get_svg_icon("copy", color=copy_icon_col))
        btn_copy.setMinimumHeight(36)
        btn_copy.clicked.connect(self._copy_to_clipboard)

        btn_close = QPushButton("Закрыть", objectName="SecondaryButton")
        btn_close.setMinimumHeight(36)
        btn_close.clicked.connect(self.accept)

        btn_box.addWidget(btn_copy, 1)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

        root_lay.addWidget(self.card)

    def _copy_to_clipboard(self):
        QApplication.clipboard().setText(self.card_number)
        ToastNotification.show_toast(self, "Номер карты скопирован в буфер обмена!", "SUCCESS")


class BeachRestDialog(QDialog):
    """Бесшовный модальный диалог морского отдыха."""

    def __init__(self, gif_path: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(540, 440)
        self.gif_path = gif_path
        self.init_ui()

    def init_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)

        self.card = HoverGlassCard()
        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        lbl_title = QLabel("Приятного отдыха!", objectName="PageTitle")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        btn_x = QPushButton("✕")
        btn_x.setFixedSize(28, 28)
        btn_x.setCursor(Qt.PointingHandCursor)
        btn_x.setStyleSheet("QPushButton { background: rgba(255, 255, 255, 0.07); color: #94A3B8; border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 8px; font-size: 13px; font-weight: bold; } QPushButton:hover { background: rgba(239, 68, 68, 0.45); color: #FFFFFF; }")
        btn_x.clicked.connect(self.accept)

        header_row.addWidget(lbl_title, 1)
        header_row.addWidget(btn_x)
        layout.addLayout(header_row)

        card_inner = HoverGlassCard()
        card_lay = QVBoxLayout(card_inner)
        card_lay.setContentsMargins(8, 8, 8, 8)

        self.lbl_gif = QLabel()
        self.lbl_gif.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_gif.setStyleSheet("background: transparent;")

        if os.path.exists(self.gif_path):
            self.movie = QMovie(self.gif_path)
            self.lbl_gif.setMovie(self.movie)
            self.movie.start()
        else:
            self.lbl_gif.setText("Файл анимации пляжа не найден")
            self.lbl_gif.setStyleSheet("color: #F87171; font-size: 13px;")

        card_lay.addWidget(self.lbl_gif)
        layout.addWidget(card_inner, 1)

        btn_close = QPushButton("Вернуться к работе", objectName="PrimaryButton")
        btn_close.setMinimumHeight(36)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        root_lay.addWidget(self.card)

    def closeEvent(self, event):
        if hasattr(self, 'movie') and self.movie:
            self.movie.stop()
        super().closeEvent(event)


class AboutPage(QWidget):
    """Экран сведений о системе и кастомизации 3D-волн и минимализма."""

    def __init__(self, main_win=None):
        super().__init__()
        self.main_win = main_win
        self.setObjectName("AboutPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(14)

        title = QLabel("О программе и Настройки 3D-волн", objectName="PageTitle")
        root_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. Сведения о системе
        self.info_card = HoverGlassCard()
        info_lay = QVBoxLayout(self.info_card)
        info_lay.setContentsMargins(24, 20, 24, 20)
        info_lay.setSpacing(10)

        accent = ThemeManager.get_current_accent_color()
        self.glass_app_icon = GlassIconWidget("droplet", accent, size=QSize(48, 48))

        app_header_lay = QHBoxLayout()
        app_header_lay.setSpacing(14)
        app_header_lay.addWidget(self.glass_app_icon)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)
        self.appName_label = QLabel("WaterMetrics Professional Edition")
        self.appName_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {accent};")
        sub = QLabel("Система автоматизированного расчета и распределения объемов водопотребления")
        sub.setStyleSheet("font-size: 13px; color: #94A3B8;")
        title_vbox.addWidget(self.appName_label)
        title_vbox.addWidget(sub)

        app_header_lay.addLayout(title_vbox, 1)
        info_lay.addLayout(app_header_lay)

        ver = QLabel(f"Версия: v{APP_VERSION} (PySide6 Apple Frosted Glass & 3D Wave Edition)")
        ver.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 600;")

        btns = QHBoxLayout()
        btns.setSpacing(10)

        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        self.btn_check_update = QPushButton("Проверить обновления", objectName="PrimaryButton")
        self.btn_check_update.setIcon(get_svg_icon("update", color="#020617" if not is_light else "#FFFFFF"))
        self.btn_check_update.clicked.connect(self.check_updates)

        self.btn_onboarding = QPushButton("Обучение проводке", objectName="SecondaryButton")
        self.btn_onboarding.setIcon(get_svg_icon("sparkles"))
        self.btn_onboarding.clicked.connect(self.restart_onboarding)

        self.btn_donate = QPushButton("Поддержка", objectName="SecondaryButton")
        self.btn_donate.setIcon(get_svg_icon("about"))
        self.btn_donate.clicked.connect(self.show_donate)

        self.btn_beach = QPushButton("Морской Отдых", objectName="AccentButton")
        self.btn_beach.setIcon(get_svg_icon("run"))
        self.btn_beach.clicked.connect(self.show_beach)

        btns.addWidget(self.btn_check_update)
        btns.addWidget(self.btn_onboarding)
        btns.addWidget(self.btn_donate)
        btns.addWidget(self.btn_beach)
        btns.addStretch()

        info_lay.addWidget(ver)
        info_lay.addLayout(btns)
        layout.addWidget(self.info_card)

        # 2. Карточка обновлений через GitHub
        self.update_card = HoverGlassCard()
        update_lay = QVBoxLayout(self.update_card)
        update_lay.setContentsMargins(24, 20, 24, 20)
        update_lay.setSpacing(12)

        lbl_upd_head = QLabel("🚀 Удаленные обновления ПО (GitHub Releases)", objectName="SectionTitle")
        lbl_upd_head.setStyleSheet("font-size: 16px; font-weight: 700;")
        update_lay.addWidget(lbl_upd_head)

        upd_settings = QSettings("WaterMetrics", "Updates")
        saved_repo = upd_settings.value("GitHubRepo", DEFAULT_GITHUB_REPO, type=str)
        auto_check = upd_settings.value("AutoCheckUpdates", True, type=bool)

        repo_row = QHBoxLayout()
        repo_row.setSpacing(10)
        lbl_repo = QLabel("Репозиторий GitHub:")
        lbl_repo.setStyleSheet("font-size: 12px; color: #94A3B8; font-weight: 600;")
        self.txt_repo = QLineEdit(saved_repo)
        self.txt_repo.setPlaceholderText("owner/repository")
        self.txt_repo.setMinimumHeight(32)
        self.txt_repo.textChanged.connect(self._on_repo_text_changed)

        self.btn_card_check = QPushButton("Проверить сейчас", objectName="PrimaryButton")
        self.btn_card_check.setIcon(get_svg_icon("update", color="#020617" if not is_light else "#FFFFFF"))
        self.btn_card_check.setMinimumHeight(32)
        self.btn_card_check.clicked.connect(self.check_updates)

        repo_row.addWidget(lbl_repo)
        repo_row.addWidget(self.txt_repo, 1)
        repo_row.addWidget(self.btn_card_check)
        update_lay.addLayout(repo_row)

        self.chk_auto_updates = QCheckBox("Автоматически проверять обновления при каждом запуске")
        self.chk_auto_updates.setChecked(auto_check)
        self.chk_auto_updates.toggled.connect(self._on_auto_check_toggled)
        update_lay.addWidget(self.chk_auto_updates)

        self.lbl_update_status = QLabel("Статус: нажмите «Проверить обновления» для запроса последнего релиза с GitHub.")
        self.lbl_update_status.setStyleSheet("font-size: 12px; color: #64748B;")
        update_lay.addWidget(self.lbl_update_status)

        layout.addWidget(self.update_card)

        # 2. Кастомизация 3D водяных волн
        self.wave_card = HoverGlassCard()
        wave_lay = QVBoxLayout(self.wave_card)
        wave_lay.setContentsMargins(24, 20, 24, 20)
        wave_lay.setSpacing(14)

        lbl_wave_head = QLabel("🌊 Редактор 3D-волн заднего плана (OpenGL)", objectName="SectionTitle")
        lbl_wave_head.setStyleSheet("font-size: 16px; font-weight: 700;")
        wave_lay.addWidget(lbl_wave_head)

        wave_settings = QSettings("WaterMetrics", "WaveSettings")
        init_waves_enabled = wave_settings.value("WavesEnabled", True, type=bool)
        init_density = wave_settings.value("GridDensity", 30, type=int)
        init_opacity = wave_settings.value("LineOpacity", 28, type=int)
        init_amp = wave_settings.value("WaveAmplitude", 100, type=int)
        init_speed = wave_settings.value("WaveSpeed", 10, type=int)
        init_tilt = wave_settings.value("WaveTilt", 48, type=int)

        self.chk_enable_waves = QCheckBox("Отображать 3D-сетку волн (OpenGL background)")
        self.chk_enable_waves.setStyleSheet(f"color: {accent}; font-weight: bold; font-size: 13px;")
        self.chk_enable_waves.setChecked(init_waves_enabled)
        self.chk_enable_waves.toggled.connect(self._on_waves_enabled_toggled)
        wave_lay.addWidget(self.chk_enable_waves)

        grid_wave = QGridLayout()
        grid_wave.setSpacing(12)

        # Плотность сетки (4 до 60 квадратов)
        lbl_density_t = QLabel("Плотность сетки (от 4×4):", objectName="FieldLabel")
        self.lbl_density_val = QLabel(f"{init_density} x {init_density}")
        self.lbl_density_val.setStyleSheet(f"color: {accent}; font-weight: bold;")
        self.sld_density = QSlider(Qt.Orientation.Horizontal)
        self.sld_density.setRange(4, 60)
        self.sld_density.setValue(init_density)
        self.sld_density.valueChanged.connect(self._on_density_changed)

        # Прозрачность линий (0% до 100% - можно полностью убрать)
        lbl_opacity_t = QLabel("Прозрачность линий (0% - полностью скрыть):", objectName="FieldLabel")
        self.lbl_opacity_val = QLabel(f"{init_opacity}%")
        self.lbl_opacity_val.setStyleSheet(f"color: {accent}; font-weight: bold;")
        self.sld_opacity = QSlider(Qt.Orientation.Horizontal)
        self.sld_opacity.setRange(0, 100)
        self.sld_opacity.setValue(init_opacity)
        self.sld_opacity.valueChanged.connect(self._on_opacity_changed)

        # Интенсивность / Амплитуда волн
        lbl_amp_t = QLabel("Интенсивность волн (высота):", objectName="FieldLabel")
        self.lbl_amp_val = QLabel(f"{init_amp}%")
        self.lbl_amp_val.setStyleSheet(f"color: {accent}; font-weight: bold;")
        self.sld_amp = QSlider(Qt.Orientation.Horizontal)
        self.sld_amp.setRange(0, 200)
        self.sld_amp.setValue(init_amp)
        self.sld_amp.valueChanged.connect(self._on_amp_changed)

        # Скорость движения волн
        lbl_speed_t = QLabel("Скорость анимации волн:", objectName="FieldLabel")
        self.lbl_speed_val = QLabel(f"{init_speed / 10.0:.1f}x")
        self.lbl_speed_val.setStyleSheet(f"color: {accent}; font-weight: bold;")
        self.sld_speed = QSlider(Qt.Orientation.Horizontal)
        self.sld_speed.setRange(0, 30)
        self.sld_speed.setValue(init_speed)
        self.sld_speed.valueChanged.connect(self._on_speed_changed)

        # Наклон сетки
        lbl_tilt_t = QLabel("Наклон 3D сетки:", objectName="FieldLabel")
        self.lbl_tilt_val = QLabel(f"{init_tilt}°")
        self.lbl_tilt_val.setStyleSheet(f"color: {accent}; font-weight: bold;")
        self.sld_tilt = QSlider(Qt.Orientation.Horizontal)
        self.sld_tilt.setRange(10, 90)
        self.sld_tilt.setValue(init_tilt)
        self.sld_tilt.valueChanged.connect(self._on_tilt_changed)

        grid_wave.addWidget(lbl_density_t, 0, 0)
        grid_wave.addWidget(self.sld_density, 0, 1)
        grid_wave.addWidget(self.lbl_density_val, 0, 2)

        grid_wave.addWidget(lbl_opacity_t, 1, 0)
        grid_wave.addWidget(self.sld_opacity, 1, 1)
        grid_wave.addWidget(self.lbl_opacity_val, 1, 2)

        grid_wave.addWidget(lbl_amp_t, 2, 0)
        grid_wave.addWidget(self.sld_amp, 2, 1)
        grid_wave.addWidget(self.lbl_amp_val, 2, 2)

        grid_wave.addWidget(lbl_speed_t, 3, 0)
        grid_wave.addWidget(self.sld_speed, 3, 1)
        grid_wave.addWidget(self.lbl_speed_val, 3, 2)

        grid_wave.addWidget(lbl_tilt_t, 4, 0)
        grid_wave.addWidget(self.sld_tilt, 4, 1)
        grid_wave.addWidget(self.lbl_tilt_val, 4, 2)

        wave_lay.addLayout(grid_wave)
        layout.addWidget(self.wave_card)

        # 3. Видимость элементов интерфейса (Минимализм)
        self.vis_card = HoverGlassCard()
        vis_lay = QVBoxLayout(self.vis_card)
        vis_lay.setContentsMargins(24, 20, 24, 20)
        vis_lay.setSpacing(12)

        lbl_vis_head = QLabel("👁 Отображение элементов Главного экрана (Минимализм)", objectName="SectionTitle")
        lbl_vis_head.setStyleSheet("font-size: 16px; font-weight: 700;")
        vis_lay.addWidget(lbl_vis_head)

        grid_vis = QGridLayout()
        grid_vis.setSpacing(12)

        ui_vis_settings = QSettings("WaterMetrics", "UIVisibility")

        self.chk_vis_kpi = QCheckBox("Панель KPI метрик расхода")
        self.chk_vis_kpi.setChecked(ui_vis_settings.value("VisKPI", True, type=bool))
        self.chk_vis_kpi.toggled.connect(self._toggle_kpi_visibility)

        self.chk_vis_files = QCheckBox("Карточка загрузки файлов (Шаблон / Аркус)")
        self.chk_vis_files.setChecked(ui_vis_settings.value("VisFiles", True, type=bool))
        self.chk_vis_files.toggled.connect(self._toggle_files_visibility)

        self.chk_vis_targets = QCheckBox("Карточка параметров ХВС / ГВС / ДОБ.")
        self.chk_vis_targets.setChecked(ui_vis_settings.value("VisTargets", True, type=bool))
        self.chk_vis_targets.toggled.connect(self._toggle_targets_visibility)

        self.chk_vis_hist = QCheckBox("Карточка истории сгенерированных отчетов")
        self.chk_vis_hist.setChecked(ui_vis_settings.value("VisHist", True, type=bool))
        self.chk_vis_hist.toggled.connect(self._toggle_hist_visibility)

        self.chk_vis_control = QCheckBox("Нижняя плавающая панель запуска расчетов")
        self.chk_vis_control.setChecked(ui_vis_settings.value("VisControl", True, type=bool))
        self.chk_vis_control.toggled.connect(self._toggle_control_visibility)

        self.chk_vis_title = QCheckBox("Верхняя панель кастомного заголовка окна")
        self.chk_vis_title.setChecked(ui_vis_settings.value("VisTitle", True, type=bool))
        self.chk_vis_title.toggled.connect(self._toggle_title_visibility)

        grid_vis.addWidget(self.chk_vis_kpi, 0, 0)
        grid_vis.addWidget(self.chk_vis_files, 0, 1)
        grid_vis.addWidget(self.chk_vis_targets, 1, 0)
        grid_vis.addWidget(self.chk_vis_hist, 1, 1)
        grid_vis.addWidget(self.chk_vis_control, 2, 0)
        grid_vis.addWidget(self.chk_vis_title, 2, 1)

        vis_lay.addLayout(grid_vis)
        layout.addWidget(self.vis_card)

        scroll.setWidget(scroll_content)
        root_layout.addWidget(scroll, 1)

        ThemeManager.on_theme_changed.append(self.update_theme_elements)
        self.update_theme_elements()

    def showEvent(self, event):
        super().showEvent(event)
        self.update_theme_elements()

    def update_theme_elements(self, theme_name: str = None):
        curr_theme = theme_name or ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        accent = ThemeManager.get_current_accent_color()
        if hasattr(self, 'glass_app_icon'):
            self.glass_app_icon.set_color(accent)
        if hasattr(self, 'appName_label'):
            title_col = "#0A246A" if curr_theme == "Как дома" else ("#0F172A" if curr_theme == "Pearl Light" else accent)
            self.appName_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {title_col};")
        if hasattr(self, 'chk_enable_waves'):
            chk_col = "#0A246A" if curr_theme == "Как дома" else ("#028090" if curr_theme == "Pearl Light" else accent)
            self.chk_enable_waves.setStyleSheet(f"color: {chk_col}; font-weight: bold; font-size: 13px;")
        for attr_name in ('lbl_density_val', 'lbl_opacity_val', 'lbl_amp_val', 'lbl_speed_val', 'lbl_tilt_val'):
            if hasattr(self, attr_name):
                val_col = "#0A246A" if curr_theme == "Как дома" else ("#028090" if curr_theme == "Pearl Light" else accent)
                getattr(self, attr_name).setStyleSheet(f"color: {val_col}; font-weight: bold;")

        if hasattr(self, 'btn_beach'):
            if curr_theme == "Как дома":
                self.btn_beach.setStyleSheet("QPushButton#AccentButton { background-color: #005A9E; color: #FFFFFF; font-weight: bold; font-size: 12px; border: 1px solid #003D7A; border-radius: 3px; padding: 6px 14px; min-height: 22px; } QPushButton#AccentButton:hover { background-color: #0068B4; }")
                self.btn_beach.setIcon(get_svg_icon("run", color="#FFFFFF"))
            elif curr_theme == "Pearl Light":
                self.btn_beach.setStyleSheet("QPushButton#AccentButton { background-color: #028090; color: #FFFFFF; font-weight: bold; font-size: 12px; border: none; border-radius: 10px; padding: 6px 14px; min-height: 22px; } QPushButton#AccentButton:hover { background-color: #026C7A; }")
                self.btn_beach.setIcon(get_svg_icon("run", color="#FFFFFF"))
            else:
                self.btn_beach.setStyleSheet("")
                self.btn_beach.setIcon(get_svg_icon("run", color="#020617"))

        if hasattr(self, 'btn_donate'):
            donate_icon_col = "#0A246A" if curr_theme == "Как дома" else ("#028090" if curr_theme == "Pearl Light" else "#94A3B8")
            self.btn_donate.setIcon(get_svg_icon("about", color=donate_icon_col))

        card_bgs = {
            "Dark Tech Azure": ("#0B1736", "#00F2FE", "18px"),
            "Cyberpunk Neon": ("#240536", "#FF007F", "18px"),
            "Emerald Cyber": ("#062618", "#10B981", "18px"),
            "Deep Violet Glass": ("#180A38", "#A855F7", "18px"),
            "Pearl Light": ("#F8FAFC", "#028090", "18px"),
            "Как дома": ("#FFFFFF", "#7F9DB9", "2px"),
        }
        bg, border, rad = card_bgs.get(curr_theme, ("#0B1736", accent, "18px"))
        card_style = f"QFrame#GlassCard {{ background-color: {bg}; border: 1.5px solid {border}; border-radius: {rad}; }}"

        for card_name in ('info_card', 'wave_card', 'vis_card'):
            if hasattr(self, card_name):
                c = getattr(self, card_name)
                c.setStyleSheet(card_style)
                c.style().unpolish(c)
                c.style().polish(c)
                c.update()

    def _get_ocean(self):
        win = self.window()
        if win and hasattr(win, 'ocean_bg'):
            return win.ocean_bg
        return None

    def _get_page_main(self):
        win = self.window()
        if win and hasattr(win, 'page_main'):
            return win.page_main
        return None

    def _on_waves_enabled_toggled(self, enabled: bool):
        ocean = self._get_ocean()
        if ocean and hasattr(ocean, 'set_waves_enabled'):
            ocean.set_waves_enabled(enabled)
        else:
            QSettings("WaterMetrics", "WaveSettings").setValue("WavesEnabled", enabled)

    def _on_density_changed(self, val: int):
        self.lbl_density_val.setText(f"{val} x {val}")
        ocean = self._get_ocean()
        if ocean and hasattr(ocean, 'set_grid_density'):
            ocean.set_grid_density(val)
        else:
            QSettings("WaterMetrics", "WaveSettings").setValue("GridDensity", val)

    def _on_opacity_changed(self, val: int):
        self.lbl_opacity_val.setText(f"{val}%")
        ocean = self._get_ocean()
        if ocean and hasattr(ocean, 'set_user_opacity_percent'):
            ocean.set_user_opacity_percent(val)
        elif ocean and hasattr(ocean, 'set_line_opacity'):
            ocean.set_line_opacity((val / 100.0) * 0.40)
        else:
            QSettings("WaterMetrics", "WaveSettings").setValue("LineOpacity", val)

    def _on_amp_changed(self, val: int):
        self.lbl_amp_val.setText(f"{val}%")
        ocean = self._get_ocean()
        if ocean and hasattr(ocean, 'set_wave_amplitude'):
            ocean.set_wave_amplitude((val / 100.0) * 0.22)
        else:
            QSettings("WaterMetrics", "WaveSettings").setValue("WaveAmplitude", val)

    def _on_speed_changed(self, val: int):
        spd = val / 10.0
        self.lbl_speed_val.setText(f"{spd:.1f}x")
        ocean = self._get_ocean()
        if ocean and hasattr(ocean, 'set_speed_scale'):
            ocean.set_speed_scale(spd)
        else:
            QSettings("WaterMetrics", "WaveSettings").setValue("WaveSpeed", val)

    def _on_tilt_changed(self, val: int):
        self.lbl_tilt_val.setText(f"{val}°")
        ocean = self._get_ocean()
        if ocean and hasattr(ocean, 'set_tilt'):
            ocean.set_tilt(val * 0.01)
        else:
            QSettings("WaterMetrics", "WaveSettings").setValue("WaveTilt", val)

    def _toggle_kpi_visibility(self, visible: bool):
        p = self._get_page_main()
        if p and hasattr(p, 'kpi_container'):
            p.kpi_container.setVisible(visible)
        QSettings("WaterMetrics", "UIVisibility").setValue("VisKPI", visible)

    def _toggle_files_visibility(self, visible: bool):
        p = self._get_page_main()
        if p and hasattr(p, 'card_files'):
            p.card_files.setVisible(visible)
        QSettings("WaterMetrics", "UIVisibility").setValue("VisFiles", visible)

    def _toggle_targets_visibility(self, visible: bool):
        p = self._get_page_main()
        if p and hasattr(p, 'card_targets'):
            p.card_targets.setVisible(visible)
        QSettings("WaterMetrics", "UIVisibility").setValue("VisTargets", visible)

    def _toggle_hist_visibility(self, visible: bool):
        p = self._get_page_main()
        if p and hasattr(p, 'card_hist'):
            p.card_hist.setVisible(visible)
        QSettings("WaterMetrics", "UIVisibility").setValue("VisHist", visible)

    def _toggle_control_visibility(self, visible: bool):
        p = self._get_page_main()
        if p and hasattr(p, 'control_panel'):
            p.control_panel.setVisible(visible)
        QSettings("WaterMetrics", "UIVisibility").setValue("VisControl", visible)

    def _toggle_title_visibility(self, visible: bool):
        win = self.window()
        if win and hasattr(win, 'title_bar'):
            win.title_bar.setVisible(visible)
        QSettings("WaterMetrics", "UIVisibility").setValue("VisTitle", visible)

    def show_donate(self):
        dlg = DonateDialog(self)
        dlg.exec()

    def show_beach(self):
        gif_path = get_asset_path("beach.gif")
        dlg = BeachRestDialog(gif_path, self)
        dlg.exec()

    def _on_repo_text_changed(self, text: str):
        cleaned = text.strip()
        QSettings("WaterMetrics", "Updates").setValue("GitHubRepo", cleaned)

    def _on_auto_check_toggled(self, checked: bool):
        QSettings("WaterMetrics", "Updates").setValue("AutoCheckUpdates", checked)

    def check_updates(self, silent: bool = False):
        """Запуск проверки обновлений на GitHub."""
        repo = self.txt_repo.text().strip() if hasattr(self, 'txt_repo') else DEFAULT_GITHUB_REPO
        if not repo:
            repo = DEFAULT_GITHUB_REPO

        self._silent_check = silent
        if not silent:
            if hasattr(self, 'btn_check_update'):
                self.btn_check_update.setEnabled(False)
                self.btn_check_update.setText("⏳ Проверка...")
            if hasattr(self, 'btn_card_check'):
                self.btn_card_check.setEnabled(False)
                self.btn_card_check.setText("⏳ Проверка...")

        if hasattr(self, 'lbl_update_status'):
            self.lbl_update_status.setText(f"Проверка обновлений в репозитории {repo}...")
            self.lbl_update_status.setStyleSheet("font-size: 12px; color: #00d2ff;")

        self.update_checker = GitHubUpdateChecker(repo=repo, current_ver=APP_VERSION, parent=self)
        self.update_checker.update_available.connect(self._on_update_available)
        self.update_checker.already_latest.connect(self._on_already_latest)
        self.update_checker.check_failed.connect(self._on_check_failed)
        self.update_checker.start()

    @Slot(object)
    def _on_update_available(self, release_info: GitHubReleaseInfo):
        if hasattr(self, 'btn_check_update'):
            self.btn_check_update.setEnabled(True)
            self.btn_check_update.setText("Проверить обновления")
        if hasattr(self, 'btn_card_check'):
            self.btn_card_check.setEnabled(True)
            self.btn_card_check.setText("Проверить сейчас")

        if hasattr(self, 'lbl_update_status'):
            self.lbl_update_status.setText(f"🔥 Доступна новая версия v{release_info.version}!")
            self.lbl_update_status.setStyleSheet("font-size: 12px; color: #00d890; font-weight: bold;")

        dlg = UpdateDialog(release_info, self.window() or self)
        dlg.exec()

    @Slot(str)
    def _on_already_latest(self, ver: str):
        if hasattr(self, 'btn_check_update'):
            self.btn_check_update.setEnabled(True)
            self.btn_check_update.setText("Проверить обновления")
        if hasattr(self, 'btn_card_check'):
            self.btn_card_check.setEnabled(True)
            self.btn_card_check.setText("Проверить сейчас")

        if hasattr(self, 'lbl_update_status'):
            self.lbl_update_status.setText(f"✅ У вас установлена самая свежая версия v{ver}")
            self.lbl_update_status.setStyleSheet("font-size: 12px; color: #10B981; font-weight: 600;")

        if not getattr(self, '_silent_check', False):
            ToastNotification.show_toast(self.window() or self, f"WaterMetrics v{ver} — установлена последняя версия!", "SUCCESS")

    @Slot(str)
    def _on_check_failed(self, err_msg: str):
        if hasattr(self, 'btn_check_update'):
            self.btn_check_update.setEnabled(True)
            self.btn_check_update.setText("Проверить обновления")
        if hasattr(self, 'btn_card_check'):
            self.btn_card_check.setEnabled(True)
            self.btn_card_check.setText("Проверить сейчас")

        if hasattr(self, 'lbl_update_status'):
            self.lbl_update_status.setText(f"⚠️ {err_msg}")
            self.lbl_update_status.setStyleSheet("font-size: 12px; color: #F87171;")

        if not getattr(self, '_silent_check', False):
            ToastNotification.show_toast(self.window() or self, f"Проверка обновлений: {err_msg}", "ERROR")

    def restart_onboarding(self):
        """Перезапуск интерактивного обучения первой проводке."""
        win = self.window()
        if win and hasattr(win, 'start_onboarding'):
            win.start_onboarding(force=True)