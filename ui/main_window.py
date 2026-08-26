"""
Главное окно приложения WaterMetrics.
Соблюдает контракт атрибутов/методов: switch_page, run_calculation, closed_meters, new_meters.
Включает векторные SVG-иконки для навигации.
"""

import os
import sys
import traceback
from typing import List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel,
    QPushButton, QStackedWidget, QStatusBar, QProgressBar, QDialog,
    QComboBox, QSizeGrip
)
from PySide6.QtCore import QThread, Signal, QPropertyAnimation, QEasingCurve, Qt, QSize, QSettings, QEvent, QTimer
from PySide6.QtGui import QShortcut, QKeySequence

from core.calculator import WaterCalculator
from core.excel_parser import ExcelManager
from models import CalculationConfig, ClosedMeterRecord, NewMeterRecord

from ui.styles import ThemeManager, get_svg_icon
from ui.dashboard_page import MainDashboardPage
from ui.norms_page import NormsPage
from ui.logs_page import LogsPage
from ui.test_tab import AutoTestsPage
from ui.about_page import AboutPage
from ui.components.toast import ToastNotification
from ui.dialogs.replacement_dialog import MeterReplacementDialog
from ui.dialogs.command_palette import CommandPaletteDialog
from ui.dialogs.welcome_dialog import WelcomeSetupDialog
from ui.components.progress_overlay import CalculationProgressOverlay
from ui.components.onboarding_overlay import OnboardingOverlay, OnboardingStep
from ui.components.companion_dock import CompanionModeManager
from ui.gl.ocean_widget import OceanWidget


class CalculationWorker(QThread):
    log_signal = Signal(str, str)
    finished_signal = Signal(bool, str)
    file_created_signal = Signal(str)

    def __init__(self, config: CalculationConfig, excel_manager: ExcelManager):
        super().__init__()
        self.config = config
        self.excel_manager = excel_manager

    def run(self):
        try:
            wb, ws, meters, meter_by_type, all_rows, non_apts, name_col = self.excel_manager.extract_data(
                self.config.template_path, self.config.arcus_path
            )
            calc = WaterCalculator(self.config, lambda msg, level="INFO": self.log_signal.emit(msg, level), lambda msg: True)
            calc.calculate(all_rows, meters, meter_by_type)

            self.excel_manager.save_result(
                wb, ws, self.config.save_path, meters, all_rows, non_apts, name_col,
                self.config.closed_meters, self.config.new_meters
            )
            self.file_created_signal.emit(self.config.save_path)
            self.finished_signal.emit(True, "Файл успешно сформирован!")
        except Exception as e:
            self.log_signal.emit(f"Ошибка: {e}\n{traceback.format_exc()}", "ERROR")
            self.finished_signal.emit(False, str(e))


class CollapsibleSidebar(QFrame):
    """Сворачиваемый боковой сайдбар с векторными SVG-иконками."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarPanel")
        self.is_collapsed = False
        self.expanded_w = 220
        self.collapsed_w = 60

        self.setFixedWidth(self.expanded_w)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 16, 10, 16)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setContentsMargins(4, 0, 4, 10)

        self.lbl_brand = QLabel("WaterMetrics")
        accent = ThemeManager.get_current_accent_color()
        self.lbl_brand.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {accent};")

        self.btn_toggle = QPushButton("", objectName="SecondaryButton")
        self.btn_toggle.setIcon(get_svg_icon("toggle", color="#F8FAFC"))
        self.btn_toggle.setIconSize(QSize(18, 18))
        self.btn_toggle.setFixedSize(34, 34)
        self.btn_toggle.setToolTip("Свернуть / развернуть меню")
        self.btn_toggle.clicked.connect(self.toggle_sidebar)

        header.addWidget(self.lbl_brand)
        header.addStretch()
        header.addWidget(self.btn_toggle)
        layout.addLayout(header)

        # ─── Навигационные кнопки (всегда на первой позиции) ───
        self.nav_items_data = [
            ("Расчеты", "dashboard", 0),
            ("Нормативы", "norms", 1),
            ("Терминал логов", "logs", 2),
            ("Авто-тесты", "tests", 3),
            ("О программе", "about", 4)
        ]

        self.nav_buttons = []
        for full_text, icon_key, page_idx in self.nav_items_data:
            btn = QPushButton(f"  {full_text}")
            btn.setProperty("class", "navBtn")
            btn.setCheckable(True)

            btn.setProperty("iconKey", icon_key)
            btn.setIcon(get_svg_icon(icon_key))
            btn.setIconSize(QSize(22, 22))

            btn.setProperty("fullText", full_text)
            btn.setProperty("pageIndex", page_idx)
            btn.setFixedHeight(42)

            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addStretch()

        # ─── Подвал сайдбара: Селектор тем оформления ───
        self.lbl_theme_title = QLabel("Тема оформления:", objectName="FieldLabel")
        self.combo_theme = QComboBox()
        
        curr_theme = ThemeManager.get_current_theme_name()
        self.combo_theme.addItems(ThemeManager.get_theme_names())
        if curr_theme in ThemeManager.get_theme_names():
            self.combo_theme.setCurrentText(curr_theme)

        self.combo_theme.currentTextChanged.connect(self._on_theme_changed)

        layout.addWidget(self.lbl_theme_title)
        layout.addWidget(self.combo_theme)

        ThemeManager.on_theme_changed.append(self.update_theme_elements)
        self.update_theme_elements(curr_theme)

    def update_theme_elements(self, theme_name: str, theme_data: dict = None):
        curr_theme = theme_name or ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        accent = ThemeManager.get_current_accent_color()

        brand_color = "#0A246A" if curr_theme == "Как дома" else ("#028090" if curr_theme == "Pearl Light" else accent)
        self.lbl_brand.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {brand_color};")

        # Кнопка сворачивания меню слева (высокий контраст для Pearl Light и всех тем)
        if hasattr(self, 'btn_toggle'):
            toggle_col = "#0A246A" if curr_theme == "Как дома" else ("#028090" if curr_theme == "Pearl Light" else "#F8FAFC")
            self.btn_toggle.setIcon(get_svg_icon("toggle", color=toggle_col))
            if curr_theme == "Pearl Light":
                self.btn_toggle.setStyleSheet("QPushButton#SecondaryButton { background-color: rgba(2, 128, 144, 0.12); border: 1px solid rgba(2, 128, 144, 0.35); border-radius: 8px; } QPushButton#SecondaryButton:hover { background-color: rgba(2, 128, 144, 0.25); }")
            elif curr_theme == "Как дома":
                self.btn_toggle.setStyleSheet("QPushButton#SecondaryButton { background-color: #D4D0C8; border: 1px solid #7F9DB9; border-radius: 3px; } QPushButton#SecondaryButton:hover { background-color: #E3E0D8; }")
            else:
                self.btn_toggle.setStyleSheet("")

        # Навигационные кнопки сайдбара
        if curr_theme == "Как дома":
            nav_col = "#000000"
            nav_checked = "#FFFFFF"
        elif curr_theme == "Pearl Light":
            nav_col = "#0F172A"
            nav_checked = "#028090"
        else:
            nav_col = "#94A3B8"
            nav_checked = accent

        for btn in self.nav_buttons:
            ikey = btn.property("iconKey")
            if ikey:
                btn.setIcon(get_svg_icon(ikey, color=nav_col, checked_color=nav_checked))
        
        # Синхронизация ComboBox
        if hasattr(self, 'combo_theme'):
            self.combo_theme.blockSignals(True)
            if theme_name in ThemeManager.get_theme_names():
                self.combo_theme.setCurrentText(theme_name)
            self.combo_theme.blockSignals(False)

    def _on_theme_changed(self, theme_name: str):
        ThemeManager.apply_theme(theme_name)
        main_win = self.window()
        if main_win:
            self.repaint_all_widgets(main_win)

    def repaint_all_widgets(self, parent_widget):
        parent_widget.update()
        for child in parent_widget.findChildren(QWidget):
            child.update()
            child.style().unpolish(child)
            child.style().polish(child)

    def toggle_sidebar(self):
        will_collapse = not self.is_collapsed
        start_w = self.width()
        end_w = self.collapsed_w if will_collapse else self.expanded_w

        self.anim = QPropertyAnimation(self, b"minimumWidth")
        self.anim.setDuration(200)
        self.anim.setStartValue(start_w)
        self.anim.setEndValue(end_w)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.anim_max = QPropertyAnimation(self, b"maximumWidth")
        self.anim_max.setDuration(200)
        self.anim_max.setStartValue(start_w)
        self.anim_max.setEndValue(end_w)
        self.anim_max.setEasingCurve(QEasingCurve.Type.OutCubic)

        if will_collapse:
            self.lbl_brand.setVisible(False)
            self.lbl_theme_title.setVisible(False)
            self.combo_theme.setVisible(False)
            for btn in self.nav_buttons:
                btn.setText("")
                btn.setToolTip(btn.property("fullText"))
                btn.setStyleSheet("text-align: center; padding: 0px;")

        def on_anim_finished():
            if not will_collapse:
                self.lbl_brand.setVisible(True)
                self.lbl_theme_title.setVisible(True)
                self.combo_theme.setVisible(True)
                for btn in self.nav_buttons:
                    btn.setText(f"  {btn.property('fullText')}")
                    btn.setToolTip("")
                    btn.setStyleSheet("")

        self.anim.finished.connect(on_anim_finished)
        self.anim.start()
        self.anim_max.start()

        self.is_collapsed = will_collapse


class CustomTitleBar(QFrame):
    """Кастомный заголовок безрамочного окна с перетаскиванием и кнопками управления."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CustomTitleBar")
        self.setFixedHeight(36)
        self.setMouseTracking(True)
        self._drag_pos = None
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(8)

        self.lbl_title = QLabel("WaterMetrics Professional Edition")
        self.lbl_title.setObjectName("TitleLabel")
        self.lbl_title.setWordWrap(False)
        self.lbl_title.setMinimumWidth(240)
        layout.addWidget(self.lbl_title)

        self.btn_palette = QPushButton("[ Ctrl+K ]", objectName="TitlePaletteBtn")
        self.btn_palette.setToolTip("Палитра быстрых команд (Ctrl+K / Ctrl+P)")
        self.btn_palette.setCursor(Qt.PointingHandCursor)
        self.btn_palette.clicked.connect(self._on_palette_clicked)
        layout.addWidget(self.btn_palette)

        self.btn_companion = QPushButton("[ ◨ Набивка ]", objectName="TitlePaletteBtn")
        self.btn_companion.setToolTip("Режим набивки (Ghost Side-Dock) [F11 / Ctrl+D]")
        self.btn_companion.setCursor(Qt.PointingHandCursor)
        self.btn_companion.clicked.connect(self._on_companion_clicked)
        layout.addWidget(self.btn_companion)

        layout.addStretch()

        self.btn_min = QPushButton("—")
        self.btn_max = QPushButton("☐")
        self.btn_close = QPushButton("✕")

        for btn, name, tip in [
            (self.btn_min, "TitleMinBtn", "Свернуть"),
            (self.btn_max, "TitleMaxBtn", "Развернуть / Восстановить"),
            (self.btn_close, "TitleCloseBtn", "Закрыть")
        ]:
            btn.setObjectName(name)
            btn.setFixedSize(30, 24)
            btn.setToolTip(tip)
            layout.addWidget(btn)

        self.btn_min.clicked.connect(self._on_min)
        self.btn_max.clicked.connect(self._on_max)
        self.btn_close.clicked.connect(self._on_close)

    def _on_palette_clicked(self):
        win = self.window()
        if win and hasattr(win, '_open_command_palette'):
            win._open_command_palette()

    def _on_companion_clicked(self):
        win = self.window()
        if win and hasattr(win, 'toggle_companion_mode'):
            win.toggle_companion_mode()

    def _on_min(self):
        win = self.window()
        if win:
            win.showMinimized()

    def _on_max(self):
        win = self.window()
        if win:
            if win.isMaximized():
                win.showNormal()
                self.btn_max.setText("☐")
            else:
                win.showMaximized()
                self.btn_max.setText("❐")

    def _on_close(self):
        win = self.window()
        if win:
            win.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos is not None:
            if not self.window().isMaximized():
                self.window().move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if win:
                if win.isMaximized():
                    win.showNormal()
                    self.btn_max.setText("☐")
                else:
                    win.showMaximized()
                    self.btn_max.setText("❐")
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)


class MainWindow(QMainWindow):
    """Главное окно приложения (Frameless Edition)."""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Window
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        self.setMouseTracking(True)
        self.resize(1120, 740)
        # Минимальный размер окна — предотвращает наслаивание панелей и уход текста за экран
        self.setMinimumSize(900, 600)

        self.excel_manager = ExcelManager()
        self.closed_meters: List[ClosedMeterRecord] = []
        self.new_meters: List[NewMeterRecord] = []
        self.companion_manager = CompanionModeManager(self)

        curr_theme = ThemeManager.get_current_theme_name()
        ThemeManager.apply_theme(curr_theme)

        self.init_ui()

    def init_ui(self):
        self.ocean_bg = OceanWidget()
        self.ocean_bg.setObjectName("MainContainer")
        self.ocean_bg.setMouseTracking(True)
        self.setCentralWidget(self.ocean_bg)

        # Главный вертикальный layout: TitleBar сверху, Контент снизу
        root_v_layout = QVBoxLayout(self.ocean_bg)
        root_v_layout.setContentsMargins(0, 0, 0, 0)
        root_v_layout.setSpacing(0)

        # 1. Кастомный заголовок безрамочного окна
        self.title_bar = CustomTitleBar(self)
        root_v_layout.addWidget(self.title_bar)

        # 2. Контентная область (Сайдбар + Страницы)
        content_widget = QWidget()
        content_widget.setAutoFillBackground(False)
        content_h_layout = QHBoxLayout(content_widget)
        content_h_layout.setContentsMargins(0, 0, 0, 0)
        content_h_layout.setSpacing(0)

        self.sidebar = CollapsibleSidebar()
        self.sidebar.setMouseTracking(True)
        content_h_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setAutoFillBackground(False)
        self.stack.setObjectName("MainStack")
        self.stack.setMouseTracking(True)
        content_h_layout.addWidget(self.stack, 1)

        root_v_layout.addWidget(content_widget, 1)

        # Страницы
        self.page_main = MainDashboardPage(self)
        self.page_norms = NormsPage(self)
        self.page_logs = LogsPage(self)
        self.page_tests = AutoTestsPage(self)
        self.page_about = AboutPage(self)

        for page in (self.page_main, self.page_norms, self.page_logs,
                     self.page_tests, self.page_about):
            page.setAutoFillBackground(False)
            page.setMouseTracking(True)

        self.stack.addWidget(self.page_main)
        self.stack.addWidget(self.page_norms)
        self.stack.addWidget(self.page_logs)
        self.stack.addWidget(self.page_tests)
        self.stack.addWidget(self.page_about)

        self.status_bar = QStatusBar()
        self.status_bar.setObjectName("AppStatusBar")
        self.status_bar.setSizeGripEnabled(True)
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Система готова к работе")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setWordWrap(False)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(180)
        self.progress_bar.setVisible(False)

        self.status_bar.addWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.size_grip = QSizeGrip(self)
        self.status_bar.addPermanentWidget(self.size_grip)

        for btn in self.sidebar.nav_buttons:
            btn.clicked.connect(self._on_nav_clicked)

        self.page_norms.norms_changed.connect(self._on_norms_changed)
        self.progress_overlay = CalculationProgressOverlay(self.ocean_bg)

        # Устанавливаем event filter океана на все дочерние виджеты
        self._install_ocean_filter(self.ocean_bg)

        # Применение сохраненной видимости элементов UI
        ui_vis = QSettings("WaterMetrics", "UIVisibility")
        if hasattr(self.page_main, 'kpi_container'):
            self.page_main.kpi_container.setVisible(ui_vis.value("VisKPI", True, type=bool))
        if hasattr(self.page_main, 'card_files'):
            self.page_main.card_files.setVisible(ui_vis.value("VisFiles", True, type=bool))
        if hasattr(self.page_main, 'card_targets'):
            self.page_main.card_targets.setVisible(ui_vis.value("VisTargets", True, type=bool))
        if hasattr(self.page_main, 'card_hist'):
            self.page_main.card_hist.setVisible(ui_vis.value("VisHist", True, type=bool))
        if hasattr(self.page_main, 'control_panel'):
            self.page_main.control_panel.setVisible(ui_vis.value("VisControl", True, type=bool))
        if hasattr(self, 'title_bar'):
            self.title_bar.setVisible(ui_vis.value("VisTitle", True, type=bool))

        ThemeManager.on_theme_changed.append(self._after_theme_change)

        self._setup_shortcuts()
        self.switch_page(0)

        # Фоновые проверки и запуск онбординга после отрисовки окна
        QTimer.singleShot(900, self._on_startup_checks)

    def _install_ocean_filter(self, root: QWidget):
        for child in root.findChildren(QWidget):
            child.installEventFilter(self.ocean_bg)

    def _after_theme_change(self, theme_name: str = None, **kwargs):
        if hasattr(self, 'ocean_bg'):
            self.ocean_bg.update()
        self.update()
        for child in self.findChildren(QWidget):
            child.update()

    def _on_theme_applied(self, theme_name: str = None, **kwargs):
        self._after_theme_change(theme_name)

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+K"), self, self._open_command_palette)
        QShortcut(QKeySequence("Ctrl+P"), self, self._open_command_palette)
        QShortcut(QKeySequence("F11"), self, self.toggle_companion_mode)
        QShortcut(QKeySequence("Ctrl+D"), self, self.toggle_companion_mode)
        QShortcut(QKeySequence("Ctrl+R"), self, self.run_calculation)
        QShortcut(QKeySequence("F5"), self, self.run_calculation)
        QShortcut(QKeySequence("Ctrl+O"), self, self.page_main.drop_tpl.open_file_dialog)
        QShortcut(QKeySequence("Ctrl+L"), self, lambda: self.switch_page(2))

    def toggle_companion_mode(self):
        """Переключение между полноценным окном и правым доком режима набивки."""
        if hasattr(self, 'companion_manager'):
            if self.companion_manager.is_companion_active:
                self.companion_manager.exit_companion_mode()
            else:
                self.companion_manager.enter_companion_mode()

    def _open_command_palette(self):
        actions = [
            ("Режим набивки / Ghost Side-Dock (F11 / Ctrl+D)", "dashboard", self.toggle_companion_mode),
            ("Запустить расчет водопотребления (Ctrl+R / F5)", "run", self.run_calculation),
            ("Мастер первичной настройки (Стиль, Язык, 3D-волны)", "edit", self.open_welcome_setup),
            ("Запустить обучение (Мастер первой проводки)", "sparkles", lambda: self.start_onboarding(force=True)),
            ("Проверить обновления на GitHub", "update", lambda: self.check_for_updates(silent=False)),
            ("Переключить в Режим Аркуса (Classic)", "dashboard", self._toggle_arcus_mode),
            ("Открыть терминал логов (Ctrl+L)", "logs", lambda: self.switch_page(2)),
            ("Настроить 3D-волны и оформление", "about", lambda: self.switch_page(4)),
            ("Мастер замен счетчиков ИПУ", "replace", self.open_replacement_dialog),
            ("Загрузить файл шаблона (Ctrl+O)", "folder", self.page_main.drop_tpl.open_file_dialog),
            ("Загрузить файл Аркуса", "folder", self.page_main.drop_arc.open_file_dialog),
            ("Следующая тема оформления", "dashboard", self._cycle_theme),
            ("Сбросить сетку конструктора", "toggle", self.page_main._reset_grid)
        ]
        dlg = CommandPaletteDialog(self, actions)
        dlg.exec()

    def _toggle_arcus_mode(self):
        curr = ThemeManager.get_current_theme_name()
        if curr != "Как дома":
            ThemeManager.apply_theme("Как дома")
            ToastNotification.show_toast(self, "Активирован Режим Аркуса (Classic)", "INFO")
        else:
            ThemeManager.apply_theme("Dark Tech Azure")
            ToastNotification.show_toast(self, "Возврат к Dark Tech Azure", "SUCCESS")

    def _cycle_theme(self):
        names = ThemeManager.get_theme_names()
        curr = ThemeManager.get_current_theme_name()
        next_idx = (names.index(curr) + 1) % len(names) if curr in names else 0
        new_theme = names[next_idx]
        ThemeManager.apply_theme(new_theme)
        self.sidebar.combo_theme.setCurrentText(new_theme)
        ToastNotification.show_toast(self, f"Активирована тема: {new_theme}", "SUCCESS")

    def _on_nav_clicked(self):
        sender = self.sender()
        if sender:
            idx = sender.property("pageIndex")
            self.switch_page(idx)

    def switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.sidebar.nav_buttons):
            btn.setChecked(i == index)

    def open_replacement_dialog(self, parent_widget=None):
        tpl_path = self.page_main.drop_tpl.file_path
        if not tpl_path and hasattr(self, 'companion_manager'):
            tpl_path = self.companion_manager.win_files.tpl_path

        target_parent = parent_widget or (self if self.isVisible() else getattr(self.companion_manager, 'win_files', self))

        if not tpl_path or not os.path.exists(tpl_path):
            ToastNotification.show_toast(target_parent, "Сначала выберите файл шаблона!", "ERROR")
            return

        apts_data = self.excel_manager.extract_apartments_and_meters(tpl_path)
        dlg = MeterReplacementDialog(target_parent, apts_data, self.closed_meters, self.new_meters)
        if not self.isVisible():
            dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.closed_meters, self.new_meters = dlg.get_results()
            ToastNotification.show_toast(target_parent, f"Зафиксировано замен: {len(self.closed_meters)}", "SUCCESS")
            self.page_main._update_kpi_metrics()
            if hasattr(self, 'companion_manager'):
                self.companion_manager.update_replacements_badge()

    def _on_norms_changed(self, norm_cold: float, norm_hot: float):
        if hasattr(self, 'page_logs'):
            self.page_logs.append_log(f"Нормативы обновлены: ХВС={norm_cold:.3f} м³, ГВС={norm_hot:.3f} м³", "INFO")

    def run_calculation(self):
        if hasattr(self, 'calc_worker') and self.calc_worker and self.calc_worker.isRunning():
            ToastNotification.show_toast(self, "Расчет уже выполняется, пожалуйста, подождите...", "INFO")
            return

        tpl = self.page_main.drop_tpl.file_path
        arc = self.page_main.drop_arc.file_path
        sav = self.page_main.txt_save.text()

        if not tpl or not arc or not sav:
            ToastNotification.show_toast(self, "Укажите все пути к Excel файлам!", "ERROR")
            return

        try:
            target_cold_val = float(self.page_main.txt_cold.text().replace(',', '.'))
            target_hot_val = float(self.page_main.txt_hot.text().replace(',', '.'))
            add_val = float(self.page_main.txt_corr.text().replace(',', '.'))
            norm_c_val = float(self.page_norms.txt_norm_cold.text().replace(',', '.'))
            norm_h_val = float(self.page_norms.txt_norm_hot.text().replace(',', '.'))
            if norm_c_val > 0 and norm_h_val > 0:
                from services.settings_service import SettingsService
                SettingsService.save_norms(norm_c_val, norm_h_val)
        except ValueError:
            ToastNotification.show_toast(self, "Ошибка в числовых параметрах ввода!", "ERROR")
            return

        config = CalculationConfig(
            target_cold=target_cold_val,
            target_hot=target_hot_val,
            add_hvs=add_val,
            norm_cold=norm_c_val,
            norm_hot=norm_h_val,
            template_path=tpl,
            arcus_path=arc,
            save_path=sav,
            closed_meters=self.closed_meters,
            new_meters=self.new_meters
        )

        self.page_main.btn_run.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Выполнение расчетов...")
        self.page_main.water_gauge.set_level(0.4)

        if hasattr(self, 'progress_overlay'):
            self.progress_overlay.setVisible(True)
            self.progress_overlay.set_step(1)

        self.calc_worker = CalculationWorker(config, self.excel_manager)
        self.calc_worker.log_signal.connect(self.page_logs.append_log)
        self.calc_worker.file_created_signal.connect(self.page_main.add_history_entry)
        self.calc_worker.finished_signal.connect(self.calculation_finished)
        self.calc_worker.start()

    def calculation_finished(self, success: bool, message: str):
        self.page_main.btn_run.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Готов к работе")
        if hasattr(self, 'progress_overlay'):
            self.progress_overlay.set_step(2)
            self.progress_overlay.setVisible(False)

        if hasattr(self, 'companion_manager'):
            self.companion_manager.on_calculation_finished(success, message)

        if success:
            self.page_main.water_gauge.set_level(1.0)
            if self.isVisible():
                ToastNotification.show_toast(self, "Файл успешно сформирован!", "SUCCESS")
        else:
            if self.isVisible():
                ToastNotification.show_toast(self, f"Ошибка расчета: {message}", "ERROR")
            self.page_main.water_gauge.set_level(0.0)

    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = int(self.winId())
                GWL_STYLE = -16
                WS_MINIMIZEBOX = 0x00020000
                WS_MAXIMIZEBOX = 0x00010000
                WS_SYSMENU = 0x00080000
                user32 = ctypes.windll.user32
                style = user32.GetWindowLongPtrW(hwnd, GWL_STYLE)
                user32.SetWindowLongPtrW(hwnd, GWL_STYLE, style | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU)
            except Exception:
                pass

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if hasattr(self, 'size_grip'):
                self.size_grip.setVisible(not self.isMaximized())
            if self.isMinimized():
                if hasattr(self, 'ocean_bg') and hasattr(self.ocean_bg, 'pause_animation'):
                    self.ocean_bg.pause_animation()
            else:
                if hasattr(self, 'ocean_bg') and hasattr(self.ocean_bg, 'resume_animation'):
                    self.ocean_bg.resume_animation()
        elif event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                if hasattr(self, 'ocean_bg') and hasattr(self.ocean_bg, 'pause_animation'):
                    self.ocean_bg.pause_animation()
            else:
                if hasattr(self, 'ocean_bg') and hasattr(self.ocean_bg, 'resume_animation'):
                    self.ocean_bg.resume_animation()
        super().changeEvent(event)

    def _on_startup_checks(self):
        """Проверки при запуске приложения: первичная настройка, онбординг первого запуска и обновления."""
        welcome_done = QSettings("WaterMetrics", "WelcomeSetup").value("FirstRunSetupCompleted", False, type=bool)
        if not welcome_done:
            dlg = WelcomeSetupDialog(self)
            res = dlg.exec()
            if dlg.start_onboarding_requested:
                QTimer.singleShot(400, lambda: self.start_onboarding(force=True))
            return

        onboarding_done = QSettings("WaterMetrics", "Onboarding").value("FirstRunCompleted", False, type=bool)
        if not onboarding_done:
            self.start_onboarding(force=False)
        else:
            auto_check = QSettings("WaterMetrics", "Updates").value("AutoCheckUpdates", True, type=bool)
            if auto_check:
                self.check_for_updates(silent=True)

    def open_welcome_setup(self):
        """Открытие мастера настроек и кастомизации оформления."""
        dlg = WelcomeSetupDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.start_onboarding_requested:
            QTimer.singleShot(400, lambda: self.start_onboarding(force=True))

    def check_for_updates(self, silent: bool = False):
        """Запуск проверки обновлений через AboutPage."""
        if hasattr(self, 'page_about') and hasattr(self.page_about, 'check_updates'):
            self.page_about.check_updates(silent=silent)

    def start_onboarding(self, force: bool = False):
        """Запуск интерактивного тура обучения первой проводке."""
        if not force:
            onboarding_done = QSettings("WaterMetrics", "Onboarding").value("FirstRunCompleted", False, type=bool)
            if onboarding_done:
                return

        self.switch_page(0)

        steps = [
            OnboardingStep(
                title="1. Исходные файлы (Шаблон и Аркус)",
                description="Перетащите сюда Excel-файл шаблона прошлого месяца и файл выгрузки Аркус. Или нажмите волшебную кнопку ниже для мгновенной подстановки готовых демо-данных!",
                target_getter=lambda: getattr(self.page_main, 'card_files', None),
                show_demo_btn=True,
                page_index=0
            ),
            OnboardingStep(
                title="2. Целевые объемы и ОДН (ХВС, ГВС, ДОБ)",
                description="Введите контрольные объемы по общедомовым приборам учета. Поддерживается умная вставка сразу 3 ячеек из буфера обмена Excel (Ctrl+V)!",
                target_getter=lambda: getattr(self.page_main, 'card_targets', None),
                show_demo_btn=False,
                page_index=0
            ),
            OnboardingStep(
                title="3. Путь к итоговому файлу",
                description="Имя файла и путь для следующего месяца формируются автоматически. При желании укажите другую папку сохранения через «Обзор...».",
                target_getter=lambda: getattr(self.page_main, 'save_container', None),
                show_demo_btn=False,
                page_index=0
            ),
            OnboardingStep(
                title="4. Запуск расчета водопотребления",
                description="Нажмите кнопку «Запустить расчет» (или горячую клавишу Ctrl+R / F5) для выполнения балансировочного расчета и генерации отчета.",
                target_getter=lambda: getattr(self.page_main, 'btn_run', None),
                show_demo_btn=False,
                page_index=0
            ),
            OnboardingStep(
                title="5. Результат и История отчетов",
                description="Все сгенерированные файлы сохраняются в истории. Кликайте дважды для мгновенного открытия в Excel или используйте контекстное меню!",
                target_getter=lambda: getattr(self.page_main, 'card_hist', None),
                show_demo_btn=False,
                page_index=0
            )
        ]

        if hasattr(self, 'onboarding_overlay') and self.onboarding_overlay:
            try:
                self.onboarding_overlay.hide()
                self.onboarding_overlay.deleteLater()
            except Exception:
                pass

        overlay_parent = self.ocean_bg if hasattr(self, 'ocean_bg') else self
        self.onboarding_overlay = OnboardingOverlay(overlay_parent, steps)
        self.onboarding_overlay.demo_requested.connect(self.page_main.load_demo_data)
        self.onboarding_overlay.start()

    def closeEvent(self, event):
        if hasattr(self, 'page_main') and hasattr(self.page_main, 'save_dashboard_state'):
            self.page_main.save_dashboard_state()
        super().closeEvent(event)