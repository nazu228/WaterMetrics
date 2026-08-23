"""
Компонент плавающей и настраиваемой панели управления (DetachableControlPanel).
Поддерживает:
1. Отделение (Undocking / Floating) в отдельное функциональное окно с сохранением сигналов Qt.
2. Кастомизацию размеров (Компактный / Стандартный / Крупный) и порядка кнопок.
3. Сохранение и восстановление состояния в QSettings.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QMenu, QDialog, QLabel,
    QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QSettings, Signal, QPoint, QSize
from PySide6.QtGui import QAction, QContextMenuEvent

from ui.styles import get_svg_icon, ThemeManager


class FloatingWindowHost(QDialog):
    """Плавающее окно-контейнер при отсоединении панели управления."""
    closed_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.WindowStaysOnTopHint | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle("⚡ Панель управления WaterMetrics")
        self.setMinimumSize(340, 70)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)

    def closeEvent(self, event):
        self.closed_signal.emit()
        super().closeEvent(event)


class DetachableControlPanel(QFrame):
    """
    Панель управления с поддержкой отсоединения в плавающее окно,
    изменения порядка и масштабирования кнопок.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ControlPanelContainer")
        self.is_floating = False
        self.size_mode = "standard"  # "compact", "standard", "large"
        self.button_order = "default"  # "default", "reversed"
        self.floating_host = None

        self.parent_dashboard_widget = parent
        self.parent_dashboard_layout = None

        self.init_ui()
        self.load_settings()
        ThemeManager.on_theme_changed.append(self.update_theme_assets)
        self.update_theme_assets()

    def update_theme_assets(self, theme_name: str = None, theme_data: dict = None):
        accent = ThemeManager.get_current_accent_color()
        self.lbl_grip.setStyleSheet(f"color: {accent}; font-weight: bold; font-size: 12px; background: transparent;")
        self.btn_float_toggle.setIcon(get_svg_icon("folder", color=accent))

    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 8, 10, 8)
        self.main_layout.setSpacing(8)

        # 1. Заголовок/Grip
        self.lbl_grip = QLabel("⚡ Панель:")
        self.lbl_grip.setStyleSheet("color: #00F2FE; font-weight: bold; font-size: 12px; background: transparent;")

        # 2. Кнопка запуска (E2E-Контракт: btn_run)
        self.btn_run = QPushButton("Сформировать файл отчета", objectName="PrimaryButton")
        self.btn_run.setIcon(get_svg_icon("run", color="#020617"))
        self.btn_run.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # 3. Переключатель размера
        self.btn_size_toggle = QPushButton("", objectName="SecondaryButton")
        self.btn_size_toggle.setIcon(get_svg_icon("toggle", color="#F8FAFC"))
        self.btn_size_toggle.setToolTip("Изменить размер кнопок (Компактный / Стандартный / Крупный)")
        self.btn_size_toggle.clicked.connect(self._cycle_size_mode)

        # 4. Переключатель отсоединения (Dock/Float)
        self.btn_float_toggle = QPushButton("", objectName="SecondaryButton")
        self.btn_float_toggle.setIcon(get_svg_icon("folder", color="#00F2FE"))
        self.btn_float_toggle.setToolTip("Открепить / Прикрепить панель управления")
        self.btn_float_toggle.clicked.connect(self.toggle_floating)

        self._rebuild_layout()
        self.apply_size_mode()

    def _rebuild_layout(self):
        while self.main_layout.count() > 0:
            item = self.main_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

        self.main_layout.addWidget(self.lbl_grip)
        self.main_layout.addWidget(self.btn_run, 3)
        self.main_layout.addWidget(self.btn_size_toggle)
        self.main_layout.addWidget(self.btn_float_toggle)

    def apply_size_mode(self):
        if self.size_mode == "compact":
            h = 36
            icon_sz = QSize(16, 16)
            font_size = "11px"
        elif self.size_mode == "large":
            h = 54
            icon_sz = QSize(24, 24)
            font_size = "14px"
        else:  # "standard"
            h = 44
            icon_sz = QSize(20, 20)
            font_size = "13px"

        self.btn_run.setFixedHeight(h)
        self.btn_run.setIconSize(icon_sz)
        self.btn_run.setStyleSheet(f"font-size: {font_size}; font-weight: bold;")

        self.btn_size_toggle.setFixedSize(h, h)
        self.btn_size_toggle.setIconSize(icon_sz)

        self.btn_float_toggle.setFixedSize(h, h)
        self.btn_float_toggle.setIconSize(icon_sz)

    def _cycle_size_mode(self):
        modes = ["compact", "standard", "large"]
        idx = modes.index(self.size_mode)
        self.size_mode = modes[(idx + 1) % len(modes)]
        self.apply_size_mode()
        self.save_settings()

    def toggle_floating(self):
        if self.is_floating:
            self.dock_back()
        else:
            self.float_out()

    def float_out(self):
        if self.is_floating:
            return
        self.is_floating = True
        self.btn_float_toggle.setToolTip("Прикрепить панель обратно к окну")

        parent_w = self.parentWidget()
        if parent_w and parent_w.layout():
            self.parent_dashboard_widget = parent_w
            self.parent_dashboard_layout = parent_w.layout()
            self.parent_dashboard_layout.removeWidget(self)

        self.floating_host = FloatingWindowHost(self.window())
        self.floating_host.closed_signal.connect(self.dock_back)
        self.floating_host.layout.addWidget(self)
        self.setParent(self.floating_host)
        self.show()

        settings = QSettings("WaterMetrics", "ControlPanel")
        pos = settings.value("FloatPos", QPoint(250, 250))
        if isinstance(pos, QPoint):
            self.floating_host.move(pos)
        self.floating_host.show()
        self.save_settings()

    def dock_back(self):
        if not self.is_floating:
            return
        self.is_floating = False
        self.btn_float_toggle.setToolTip("Открепить панель в плавающее окно")

        if self.floating_host:
            settings = QSettings("WaterMetrics", "ControlPanel")
            settings.setValue("FloatPos", self.floating_host.pos())
            self.floating_host.closed_signal.disconnect(self.dock_back)
            self.floating_host.close()
            self.floating_host = None

        if self.parent_dashboard_layout:
            self.setParent(self.parent_dashboard_widget)
            self.parent_dashboard_layout.addWidget(self)
            self.show()

        self.save_settings()

    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu(self)

        act_float = QAction("📌 " + ("Прикрепить к окну" if self.is_floating else "Открепить в плавающее окно"), self)
        act_float.triggered.connect(self.toggle_floating)
        menu.addAction(act_float)

        menu.addSeparator()

        act_compact = QAction("📐 Размер: Компактный", self)
        act_compact.triggered.connect(lambda: self._set_size_mode("compact"))
        menu.addAction(act_compact)

        act_std = QAction("📐 Размер: Стандартный", self)
        act_std.triggered.connect(lambda: self._set_size_mode("standard"))
        menu.addAction(act_std)

        act_large = QAction("📐 Размер: Крупный", self)
        act_large.triggered.connect(lambda: self._set_size_mode("large"))
        menu.addAction(act_large)

        menu.exec(event.globalPos())

    def _set_size_mode(self, mode: str):
        self.size_mode = mode
        self.apply_size_mode()
        self.save_settings()

    def save_settings(self):
        settings = QSettings("WaterMetrics", "ControlPanel")
        settings.setValue("IsFloating", self.is_floating)
        settings.setValue("SizeMode", self.size_mode)
        settings.setValue("ButtonOrder", self.button_order)

    def load_settings(self):
        settings = QSettings("WaterMetrics", "ControlPanel")
        self.size_mode = settings.value("SizeMode", "standard", type=str)
        self.button_order = settings.value("ButtonOrder", "default", type=str)
        self.apply_size_mode()
        self._rebuild_layout()
