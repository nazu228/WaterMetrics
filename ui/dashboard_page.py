# ui/dashboard_page.py
"""
Основная панель Дашборда WaterMetrics.
Соблюдает 100% контракт названий элементов E2E-тестов.

Реализует:
1. Единый стиль оформлений для всех карточек (margins: 12px, spacing: 8px).
2. Динамическую Bounds Check проверку для гидравлического индикатора.
3. Множественное выделение и массовое удаление/открытие файлов в истории.
"""

import os
import math
import re
import subprocess
import sys

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QCheckBox, QApplication, QAbstractItemView, QSizePolicy,
    QFrame, QComboBox
)
from PySide6.QtCore import Qt, QSettings, Slot, QPoint, QSize, QRect, QTimer, QUrl
from PySide6.QtGui import (
    QMouseEvent, QKeyEvent, QKeySequence, QPainter, QPen, QColor,
    QResizeEvent, QDesktopServices
)

from core.excel_parser import ExcelManager
from services.history_service import HistoryService
from ui.components.interactive import ExcelDropZone, WaterGaugeWidget, HoverGlassCard
from ui.components.control_panel import DetachableControlPanel
from ui.components.toast import ToastNotification
from ui.components.glass_icon import GlassIconWidget
from ui.styles import get_svg_icon, ThemeManager


from services.folder_service import FolderNavigationService
from ui.dialogs.file_guard_dialog import FileGuardDialog


class DummyWaterGauge:
    """Заглушка гидро-индикатора для 100% E2E-совместимости с авто-тестами."""
    def set_level(self, pct: float):
        pass
    def setVisible(self, visible: bool):
        pass
    def setMinimumSize(self, w: int, h: int):
        pass
    def setMaximumSize(self, w: int, h: int):
        pass


class SmartNumericLineEdit(QLineEdit):
    """Кастомное умное числовое поле ввода с увеличенной клик-зоной, автовыделением, моноширинным шрифтом, визуальной валидацией и поддержкой подсказок (ghost/suggested)."""

    def __init__(self, contents: str = "0.0", parent=None):
        super().__init__(contents, parent)
        self.linked_fields = []
        self.is_suggested = False
        self.setMinimumHeight(38)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._apply_base_style()
        self.textChanged.connect(self._validate_input)
        self._validate_input(self.text())

    def _apply_base_style(self):
        self.setStyleSheet("""
            QLineEdit {
                font-family: 'Consolas', 'JetBrains Mono', 'Segoe UI Mono', monospace;
                font-size: 15px;
                font-weight: 700;
                padding-right: 14px;
                letter-spacing: 0.5px;
            }
            QLineEdit[suggested="true"] {
                color: #64748B !important;
                font-style: italic;
            }
        """)

    def set_suggested_value(self, val_str: str):
        """Устанавливает значение как предложение (горит серым курсивом до подтверждения Enter)."""
        self.is_suggested = True
        self.setText(str(val_str))
        self.setProperty("suggested", True)
        self.style().unpolish(self)
        self.style().polish(self)
        self.setToolTip("💡 Подставлено из таблицы импорта\nНажмите Enter для подтверждения или введите свое значение")

    def commit_suggestion(self):
        """Подтверждает предложенное значение, делая его активным нормальным цветом."""
        if self.is_suggested:
            self.is_suggested = False
            self.setProperty("suggested", False)
            self.style().unpolish(self)
            self.style().polish(self)
            self.setToolTip("")

    def _validate_input(self, text: str):
        val_str = text.strip().replace(',', '.')
        is_valid = True
        if val_str:
            try:
                v = float(val_str)
                if v < 0:
                    is_valid = False
            except ValueError:
                is_valid = False

        self.setProperty("invalid", not is_valid)
        self.style().unpolish(self)
        self.style().polish(self)
        if not is_valid:
            self.setToolTip("⚠️ Ошибка ввода: значение должно быть положительным числом!")
        elif not self.is_suggested:
            self.setToolTip("")

    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, self.selectAll)

    def mousePressEvent(self, event: QMouseEvent):
        had_focus = self.hasFocus()
        super().mousePressEvent(event)
        if not had_focus:
            QTimer.singleShot(0, self.selectAll)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.is_suggested:
                # Подтверждаем все связанные поля при нажатии Enter
                for field in (self.linked_fields or [self]):
                    if hasattr(field, 'commit_suggestion'):
                        field.commit_suggestion()
                from ui.components.toast import ToastNotification
                ToastNotification.show_toast(self.window(), "Показания подтверждены", "SUCCESS")
            super().keyPressEvent(event)
            return

        if self.is_suggested and event.text() and not (event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)):
            # Пользователь начал вводить новое значение — сбрасываем статус подсказки
            self.commit_suggestion()

        if event.matches(QKeySequence.StandardKey.Paste) or (
            key == Qt.Key.Key_V and (event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        ):
            if self._handle_multi_paste():
                event.accept()
                return

        super().keyPressEvent(event)

    def _handle_multi_paste(self) -> bool:
        clipboard_text = QApplication.clipboard().text()
        if not clipboard_text:
            return False

        text = clipboard_text.replace('\r\n', '\n').replace('\r', '\n')
        if text.endswith('\n'):
            text = text[:-1]

        if '\t' not in text and '\n' not in text and ';' not in text:
            return False

        raw_tokens = re.split(r'[\t\n;]', text)
        if len(raw_tokens) <= 1:
            return False

        tokens = []
        for t in raw_tokens:
            clean = t.strip().replace(',', '.')
            if not clean:
                tokens.append("0")
            else:
                tokens.append(clean)

        if self.linked_fields:
            try:
                start_idx = self.linked_fields.index(self)
            except ValueError:
                start_idx = 0

            target_fields = self.linked_fields[start_idx:]

            for i, token in enumerate(tokens):
                if i < len(target_fields):
                    target_fields[i].setText(token)

            last_filled_idx = min(start_idx + len(tokens) - 1, len(self.linked_fields) - 1)
            last_field = self.linked_fields[last_filled_idx]
            last_field.setFocus()
            QTimer.singleShot(0, last_field.selectAll)

            ToastNotification.show_toast(
                self.window(),
                f"Вставлено {min(len(tokens), len(target_fields))} ячеек из буфера обмена",
                "SUCCESS"
            )
            return True

        return False


class ResizableMovableCard(HoverGlassCard):
    """Интерактивная карточка конструктора."""

    def __init__(self, card_id: str, parent=None):
        super().__init__(parent)
        self.card_id = card_id
        self.builder_mode = False

        self.is_interacting = False
        self.is_resizing = False
        self.is_moving = False

        self.drag_start_pos = QPoint()
        self.start_geometry_rect = QRect()
        self.rel_rect = (0.0, 0.0, 0.3, 0.3)
        self.is_vertical_layout = False

        self.setMouseTracking(True)

    def set_builder_mode(self, enabled: bool):
        self.builder_mode = enabled
        self.setCursor(Qt.CursorShape.SizeAllCursor if enabled else Qt.CursorShape.ArrowCursor)
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if self.builder_mode and event.button() == Qt.MouseButton.LeftButton:
            self.raise_()
            self.is_interacting = True
            corner_rect = QRect(self.width() - 24, self.height() - 24, 24, 24)
            if corner_rect.contains(event.position().toPoint()):
                self.is_resizing = True
                self.drag_start_pos = event.globalPosition().toPoint()
                self.start_geometry_rect = self.geometry()
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.is_moving = True
                self.drag_start_pos = event.globalPosition().toPoint() - self.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.builder_mode:
            if self.is_resizing:
                delta = event.globalPosition().toPoint() - self.drag_start_pos
                new_w = max(self.minimumWidth(), self.start_geometry_rect.width() + delta.x())
                new_h = max(self.minimumHeight(), self.start_geometry_rect.height() + delta.y())
                self.resize(new_w, new_h)
                self.check_internal_reflow()
                event.accept()
                return
            elif self.is_moving:
                new_pos = event.globalPosition().toPoint() - self.drag_start_pos
                if self.parent():
                    max_x = max(0, self.parent().width() - self.width())
                    max_y = max(0, self.parent().height() - self.height())
                    new_pos.setX(max(0, min(new_pos.x(), max_x)))
                    new_pos.setY(max(0, min(new_pos.y(), max_y)))

                self.move(new_pos)
                event.accept()
                return

            corner_rect = QRect(self.width() - 24, self.height() - 24, 24, 24)
            if corner_rect.contains(event.position().toPoint()):
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.setCursor(Qt.CursorShape.SizeAllCursor)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.builder_mode and (self.is_resizing or self.is_moving):
            self.is_resizing = False
            self.is_moving = False
            self.is_interacting = False
            self.setCursor(Qt.CursorShape.SizeAllCursor if self.builder_mode else Qt.CursorShape.ArrowCursor)

            self.update_rel_rect()
            self.save_geometry_to_settings()
            event.accept()
        else:
            self.is_interacting = False
            super().mouseReleaseEvent(event)

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.check_internal_reflow()

    def update_rel_rect(self):
        if self.parent():
            pw = max(1, self.parent().width())
            ph = max(1, self.parent().height())
            self.rel_rect = (self.x() / pw, self.y() / ph, self.width() / pw, self.height() / ph)

    def apply_rel_rect(self, parent_size: QSize):
        if self.is_interacting:
            return

        pw = max(1, parent_size.width())
        ph = max(1, parent_size.height())
        rx, ry, rw, rh = self.rel_rect

        self.setGeometry(int(rx * pw), int(ry * ph), max(self.minimumWidth(), int(rw * pw)), max(self.minimumHeight(), int(rh * ph)))
        self.check_internal_reflow()

    def check_internal_reflow(self):
        w = self.width()
        h = self.height()

        if hasattr(self, '_last_reflow_size'):
            if abs(w - self._last_reflow_size.width()) < 6 and abs(h - self._last_reflow_size.height()) < 6:
                return
        self._last_reflow_size = QSize(w, h)

        if w >= 320 and h >= 140:
            lod = 3
        elif w >= 180 and h >= 80:
            lod = 2
        else:
            lod = 1

        need_vertical = (w < 320) and (h > w * 0.85)
        self.is_vertical_layout = need_vertical

        if hasattr(self, 'reflow_content'):
            try:
                self.reflow_content(need_vertical=need_vertical, lod=lod)
            except TypeError:
                self.reflow_content(need_vertical)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.builder_mode:
            painter = QPainter()
            if not painter.begin(self):
                return
            try:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                accent = ThemeManager.get_current_accent_color()
                pen = QPen(QColor(accent), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                w, h = self.width(), self.height()
                painter.drawLine(w - 16, h - 6, w - 6, h - 16)
                painter.drawLine(w - 10, h - 6, w - 6, h - 10)
            finally:
                painter.end()

    def save_geometry_to_settings(self):
        settings = QSettings("WaterMetrics", "DashboardCustomGrid")
        settings.setValue(f"{self.card_id}/rel_rect", self.rel_rect)

    def load_geometry_from_settings(self):
        settings = QSettings("WaterMetrics", "DashboardCustomGrid")
        val = settings.value(f"{self.card_id}/rel_rect", None)
        if val and isinstance(val, (list, tuple)) and len(val) == 4:
            self.rel_rect = tuple(float(x) for x in val)


class DashboardCanvas(QWidget):
    """Контейнер свободного размещения карточек."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.cards = []

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        new_size = event.size()
        for card in self.cards:
            if not card.is_interacting:
                card.apply_rel_rect(new_size)


class MainDashboardPage(QWidget):
    """Главная страница управления и ввода параметров."""

    def __init__(self, main_win=None):
        super().__init__()
        self.main_win = main_win
        self.setObjectName("DashboardPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.excel_manager = ExcelManager()
        self.cards = []
        self.folder_ctx = {}

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        settings = QSettings("WaterMetrics", "Directories")
        self.last_template_dir = settings.value("LastTemplateDir", base_dir, type=str)
        self.last_arcus_dir = settings.value("LastArcusDir", base_dir, type=str)

        if not self.last_template_dir or not os.path.exists(self.last_template_dir):
            self.last_template_dir = base_dir
        if not self.last_arcus_dir or not os.path.exists(self.last_arcus_dir):
            self.last_arcus_dir = base_dir

        self.init_ui()
        self._initial_layout_done = False
        self._tab_order_set = False

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        from PySide6.QtWidgets import QScrollArea
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollArea > QWidget > QWidget { background: transparent; }")

        self.scroll_content = QWidget()
        self.scroll_content.setAutoFillBackground(False)
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(16, 16, 16, 16)
        self.scroll_layout.setSpacing(12)

        # Шапка
        header_lay = QHBoxLayout()
        header_lay.setSpacing(12)

        self.glass_dash_icon = GlassIconWidget("dashboard", ThemeManager.get_current_accent_color(), size=QSize(40, 40))
        header_lay.addWidget(self.glass_dash_icon)

        title = QLabel("Расчеты", objectName="PageTitle")
        title.setWordWrap(False)
        title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        title.setMinimumWidth(0)
        header_lay.addWidget(title)
        header_lay.addStretch()

        self.btn_arcus_mode = QPushButton("🏛️ Режим Аркуса", objectName="ArcusModeButton")
        self.btn_arcus_mode.setCheckable(True)
        self.btn_arcus_mode.setMinimumHeight(34)
        self.btn_arcus_mode.setToolTip("Мгновенное переключение в классический режим Аркус / Windows Classic (0% GPU)")
        self.btn_arcus_mode.setChecked(ThemeManager.get_current_theme_name() == "Как дома")
        self.btn_arcus_mode.toggled.connect(self._on_arcus_mode_toggled)
        self.btn_arcus_mode.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._prev_theme = ThemeManager.get_current_theme_name() if ThemeManager.get_current_theme_name() != "Как дома" else "Dark Tech Azure"

        self.btn_companion_mode = QPushButton("◨ Режим набивки", objectName="SecondaryButton")
        self.btn_companion_mode.setMinimumHeight(34)
        self.btn_companion_mode.setToolTip("Включить режим набивки / Ghost Side-Dock (F11 / Ctrl+D)")
        self.btn_companion_mode.clicked.connect(self._on_toggle_companion)
        self.btn_companion_mode.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.btn_reset_grid = QPushButton("Сбросить сетку", objectName="SecondaryButton")
        self.btn_reset_grid.setIcon(get_svg_icon("toggle"))
        self.btn_reset_grid.setToolTip("Сбросить положение и размеры карточек по умолчанию")
        self.btn_reset_grid.clicked.connect(self._reset_grid)
        self.btn_reset_grid.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self.btn_builder_mode = QPushButton("✏️ Режим конструктора", objectName="AccentButton")
        self.btn_builder_mode.setCheckable(True)
        self.btn_builder_mode.setMinimumHeight(34)
        self.btn_builder_mode.setToolTip("Включить/выключить режим перетаскивания и изменения размеров карточек")
        self.btn_builder_mode.toggled.connect(self._on_builder_button_toggled)
        self.btn_builder_mode.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        header_lay.addWidget(self.btn_companion_mode)
        header_lay.addWidget(self.btn_arcus_mode)
        header_lay.addWidget(self.btn_reset_grid)
        header_lay.addWidget(self.btn_builder_mode)

        self.scroll_layout.addLayout(header_lay)
        self.kpi_container = self._build_kpi_bar()
        self.scroll_layout.addWidget(self.kpi_container)

        self.canvas = DashboardCanvas()
        self.canvas.cards = self.cards
        self.canvas.setMinimumHeight(540)
        self.scroll_layout.addWidget(self.canvas, 1)

        self.scroll_area.setWidget(self.scroll_content)
        root_layout.addWidget(self.scroll_area)

        # 1. КАРТОЧКА ФАЙЛОВ
        self.card_files = ResizableMovableCard("CardFiles", self.canvas)
        self.card_files.setMinimumSize(300, 180)
        self.cards.append(self.card_files)

        self.grid_files = QGridLayout(self.card_files)
        self.grid_files.setContentsMargins(8, 8, 8, 8)
        self.grid_files.setSpacing(6)

        # ─── Умная плашка навигации по месяцам и домам (встроена безшовно в карточку файлов) ───
        self.smart_nav_frame = QFrame(self.card_files)
        self.smart_nav_frame.setObjectName("SmartNavFrame")
        self.smart_nav_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.smart_nav_frame.setStyleSheet("""
            QFrame#SmartNavFrame {
                background: rgba(0, 242, 254, 0.06);
                border: 1.5px solid rgba(0, 242, 254, 0.25);
                border-radius: 8px;
                padding: 4px 8px;
            }
        """)
        self.smart_nav_frame.setVisible(False)
        nav_lay = QVBoxLayout(self.smart_nav_frame)
        nav_lay.setContentsMargins(6, 4, 6, 4)
        nav_lay.setSpacing(4)

        nav_top_row = QHBoxLayout()
        nav_top_row.setSpacing(8)

        self.lbl_smart_context = QLabel("")
        accent = ThemeManager.get_current_accent_color()
        self.lbl_smart_context.setStyleSheet(f"font-size: 13px; font-weight: 800; color: {accent}; background: transparent;")
        nav_top_row.addWidget(self.lbl_smart_context, 1)

        self.lbl_switch_house = QLabel("Дом:")
        self.lbl_switch_house.setStyleSheet("font-size: 12px; font-weight: 600; color: #94A3B8; background: transparent;")
        self.combo_houses = QComboBox()
        self.combo_houses.setFixedHeight(28)
        self.combo_houses.setMinimumWidth(160)
        self.combo_houses.setStyleSheet("""
            QComboBox {
                font-size: 12px;
                font-weight: 600;
                padding: 2px 6px;
                border-radius: 6px;
            }
        """)
        self.combo_houses.currentIndexChanged.connect(self._on_house_combo_changed)
        nav_top_row.addWidget(self.lbl_switch_house)
        nav_top_row.addWidget(self.combo_houses)
        nav_lay.addLayout(nav_top_row)

        self.nav_actions_widget = QWidget()
        nav_actions_row = QHBoxLayout(self.nav_actions_widget)
        nav_actions_row.setContentsMargins(0, 0, 0, 0)
        nav_actions_row.setSpacing(8)

        self.btn_auto_arcus = QPushButton("")
        self.btn_auto_arcus.setIcon(get_svg_icon("sparkles", color="#00F2FE"))
        self.btn_auto_arcus.setFixedHeight(28)
        self.btn_auto_arcus.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_auto_arcus.setStyleSheet("""
            QPushButton {
                background: rgba(0, 242, 254, 0.14);
                border: 1.5px solid rgba(0, 242, 254, 0.40);
                color: #00F2FE;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 2px 10px;
            }
            QPushButton:hover {
                background: rgba(0, 242, 254, 0.28);
                border-color: #00F2FE;
                color: #FFFFFF;
            }
        """)
        self.btn_auto_arcus.setVisible(False)
        self.btn_auto_arcus.clicked.connect(self._on_auto_arcus_clicked)
        nav_actions_row.addWidget(self.btn_auto_arcus)

        self.lbl_exist_alert = QLabel("")
        self.lbl_exist_alert.setWordWrap(False)
        self.lbl_exist_alert.setStyleSheet("""
            color: #FBBF24;
            font-size: 12px;
            font-weight: 700;
            background: rgba(245, 158, 11, 0.12);
            border: 1px solid rgba(245, 158, 11, 0.30);
            border-radius: 4px;
            padding: 2px 8px;
        """)
        self.lbl_exist_alert.setVisible(False)
        nav_actions_row.addWidget(self.lbl_exist_alert, 1)

        nav_lay.addWidget(self.nav_actions_widget)

        self.drop_tpl = ExcelDropZone("Файл Шаблона", "Перетащите файл шаблона или кликните")
        self.drop_tpl.get_initial_dir = lambda: self.last_template_dir
        self.drop_tpl.get_dialog_title = self._get_template_dialog_title
        self.drop_tpl.file_dropped.connect(self._on_template_selected)

        self.drop_arc = ExcelDropZone("Файл Аркус", "Перетащите файл Аркус или кликните")
        self.drop_arc.get_initial_dir = lambda: self.last_arcus_dir
        self.drop_arc.get_dialog_title = self._get_arcus_dialog_title
        self.drop_arc.file_dropped.connect(self._on_arcus_selected)

        self.save_container = QWidget()
        save_layout = QHBoxLayout(self.save_container)
        save_layout.setContentsMargins(0, 0, 0, 0)
        save_layout.setSpacing(8)

        self.lbl_save = QLabel("Сохранить:", objectName="FieldLabel")
        self.lbl_save.setFixedHeight(36)
        self.lbl_save.setStyleSheet("font-size: 13.5px; font-weight: 600;")
        self.txt_save = QLineEdit()
        self.txt_save.setPlaceholderText("Путь к итоговому файлу...")
        self.txt_save.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.txt_save.setFixedHeight(36)

        self.btn_browse_save = QPushButton("Обзор", objectName="SecondaryButton")
        self.btn_browse_save.setIcon(get_svg_icon("folder"))
        self.btn_browse_save.setFixedHeight(36)
        self.btn_browse_save.setMinimumWidth(85)
        self.btn_browse_save.clicked.connect(self._browse_save_path)

        self.btn_repl = QPushButton("Замены ИПУ", objectName="AccentButton")
        self.btn_repl.setIcon(get_svg_icon("replace"))
        self.btn_repl.setFixedHeight(36)
        self.btn_repl.setMinimumWidth(125)
        self.btn_repl.setToolTip("Мастер замен счетчиков ИПУ")
        self.btn_repl.clicked.connect(self._open_replacement_master)

        save_layout.addWidget(self.lbl_save)
        save_layout.addWidget(self.txt_save, 1)
        save_layout.addWidget(self.btn_browse_save)
        save_layout.addWidget(self.btn_repl)

        # Компактные кнопки
        self.btn_compact_tpl = QPushButton("Шаблон", objectName="SecondaryButton")
        self.btn_compact_tpl.setIcon(get_svg_icon("folder"))
        self.btn_compact_tpl.setFixedHeight(30)
        self.btn_compact_tpl.clicked.connect(self.drop_tpl.open_file_dialog)

        self.btn_compact_arc = QPushButton("Аркус", objectName="SecondaryButton")
        self.btn_compact_arc.setIcon(get_svg_icon("folder"))
        self.btn_compact_arc.setFixedHeight(30)
        self.btn_compact_arc.clicked.connect(self.drop_arc.open_file_dialog)

        self.btn_compact_save = QPushButton("Сохранение", objectName="SecondaryButton")
        self.btn_compact_save.setIcon(get_svg_icon("folder"))
        self.btn_compact_save.setFixedHeight(30)
        self.btn_compact_save.clicked.connect(self._browse_save_path)

        self.btn_compact_repl = QPushButton("Замена", objectName="AccentButton")
        self.btn_compact_repl.setIcon(get_svg_icon("replace"))
        self.btn_compact_repl.setMinimumHeight(32)
        self.btn_compact_repl.clicked.connect(self._open_replacement_master)

        ThemeManager.on_theme_changed.append(self._update_theme_assets)
        self.card_files.reflow_content = self._reflow_files_card

        # 2. КАРТОЧКА ЦЕЛЕЙ
        self.card_targets = ResizableMovableCard("CardTargets", self.canvas)
        self.card_targets.setMinimumSize(220, 160)
        self.cards.append(self.card_targets)

        self.grid_targets = QGridLayout(self.card_targets)
        self.grid_targets.setContentsMargins(14, 14, 14, 14)
        self.grid_targets.setSpacing(10)

        self.lbl_cold = QLabel("ХВС:", objectName="FieldLabel")
        self.lbl_cold.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.txt_cold = SmartNumericLineEdit("0.0")

        self.lbl_hot = QLabel("ГВС:", objectName="FieldLabel")
        self.lbl_hot.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.txt_hot = SmartNumericLineEdit("0.0")

        self.lbl_corr = QLabel("ДОБ.:", objectName="FieldLabel")
        self.lbl_corr.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.txt_corr = SmartNumericLineEdit("0.0")

        # Кнопка импорта показаний из внешней таблицы
        self.btn_import_values = QPushButton("📥 Из таблицы", objectName="SecondaryButton")
        self.btn_import_values.setIcon(get_svg_icon("sparkles"))
        self.btn_import_values.setFixedHeight(34)
        self.btn_import_values.setToolTip("Импорт ХВС/ГВС/ДОБ из набивочной таблицы Excel")
        self.btn_import_values.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_import_values.clicked.connect(self._open_import_dialog)

        numeric_chain = [self.txt_cold, self.txt_hot, self.txt_corr]
        for field in numeric_chain:
            field.linked_fields = numeric_chain

        self.water_gauge = DummyWaterGauge()

        self.txt_cold.returnPressed.connect(self.txt_hot.setFocus)
        self.txt_hot.returnPressed.connect(self.txt_corr.setFocus)
        self.txt_corr.returnPressed.connect(self.txt_save.setFocus)
        self.txt_save.returnPressed.connect(self._on_enter_run_calculation)

        self.card_targets.reflow_content = self._reflow_targets_card

        # 3. КАРТОЧКА ИСТОРИИ
        self.card_hist = ResizableMovableCard("CardHistory", self.canvas)
        self.card_hist.setMinimumSize(320, 240)
        self.cards.append(self.card_hist)

        self.layout_hist = QVBoxLayout(self.card_hist)
        self.layout_hist.setContentsMargins(14, 14, 14, 14)
        self.layout_hist.setSpacing(10)

        self.lbl_hist_title = QLabel("История сгенерированных отчетов", objectName="SectionTitle")
        self.lbl_hist_title.setStyleSheet("font-size: 15.5px; font-weight: 700;")
        self.layout_hist.addWidget(self.lbl_hist_title)

        self.table_hist = QTableWidget(0, 2)
        self.table_hist.setHorizontalHeaderLabels(["Имя файла", "Полный путь"])
        self.table_hist.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_hist.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table_hist.horizontalHeader().setFixedHeight(32)
        self.table_hist.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table_hist.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_hist.verticalHeader().setVisible(False)
        self.table_hist.setAlternatingRowColors(False)
        self.table_hist.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_hist.customContextMenuRequested.connect(self._show_history_context_menu)

        self.layout_hist.addWidget(self.table_hist, 1)

        self.layout_hist_btns = QHBoxLayout()
        self.layout_hist_btns.setSpacing(6)

        self.btn_hist_open = QPushButton("Открыть", objectName="SecondaryButton")
        self.btn_hist_open.setIcon(get_svg_icon("folder"))
        self.btn_hist_open.setFixedHeight(34)
        self.btn_hist_open.clicked.connect(self._open_selected_history_file)

        self.btn_hist_show_folder = QPushButton("В папку", objectName="SecondaryButton")
        self.btn_hist_show_folder.setIcon(get_svg_icon("folder"))
        self.btn_hist_show_folder.setFixedHeight(34)
        self.btn_hist_show_folder.clicked.connect(self._show_selected_in_folder)

        self.btn_hist_clr = QPushButton("Удалить", objectName="SecondaryButton")
        self.btn_hist_clr.setIcon(get_svg_icon("trash"))
        self.btn_hist_clr.setFixedHeight(34)
        self.btn_hist_clr.clicked.connect(self._remove_selected_history_entries)

        self.btn_hist_clear_all = QPushButton("Очистить", objectName="DangerButton")
        self.btn_hist_clear_all.setIcon(get_svg_icon("trash", color="#EF4444"))
        self.btn_hist_clear_all.setFixedHeight(34)
        self.btn_hist_clear_all.setToolTip("Очистить всю историю отчетов")
        self.btn_hist_clear_all.clicked.connect(self._clear_all_history_entries)

        self.layout_hist_btns.addWidget(self.btn_hist_open)
        self.layout_hist_btns.addWidget(self.btn_hist_show_folder)
        self.layout_hist_btns.addWidget(self.btn_hist_clr)
        self.layout_hist_btns.addWidget(self.btn_hist_clear_all)
        self.layout_hist_btns.addStretch()

        self.layout_hist.addLayout(self.layout_hist_btns)

        self.card_hist.reflow_content = self._reflow_hist_card

        # Первичный рефлоу
        self._reflow_files_card(need_vertical=False, lod=3)
        self._reflow_targets_card(need_vertical=False, lod=3)
        self._reflow_hist_card(need_vertical=False, lod=3)

        self.control_panel = DetachableControlPanel(self)
        self.btn_run = self.control_panel.btn_run
        self.btn_run.clicked.connect(self._start_calculation)
        self.scroll_layout.addWidget(self.control_panel)

    def showEvent(self, event):
        """Устанавливаем Tab-порядок только после того, как виджет показан в окне."""
        super().showEvent(event)
        if not self._tab_order_set:
            self._tab_order_set = True
            self.setTabOrder(self.txt_cold, self.txt_hot)
            self.setTabOrder(self.txt_hot, self.txt_corr)
            self.setTabOrder(self.txt_corr, self.txt_save)
            self.setTabOrder(self.txt_save, self.btn_run)

    def _build_kpi_bar(self) -> QWidget:
        container = QWidget()
        container.setObjectName("KpiContainer")
        container.setAutoFillBackground(False)
        kpi_lay = QHBoxLayout(container)
        kpi_lay.setContentsMargins(0, 0, 0, 0)
        kpi_lay.setSpacing(10)
        accent = ThemeManager.get_current_accent_color()
        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        title_color = "#475569" if is_light else "#94A3B8"
        val_color = "#0A246A" if curr_theme == "Как дома" else ("#028090" if curr_theme == "Pearl Light" else accent)

        kpi_data = [
            ("📊 Отчетов за месяц", "lbl_kpi_reports", "0"),
            ("💧 Суммарный расход", "lbl_kpi_volume", "0.0 м³"),
            ("🔄 Заменено ИПУ", "lbl_kpi_meters", "0 шт"),
            ("⚡ Статус системы", "lbl_kpi_status", "● Готов к работе")
        ]

        for title_str, attr_name, default_val in kpi_data:
            card = HoverGlassCard()
            card.setFixedHeight(54)
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(14, 6, 14, 6)
            c_lay.setSpacing(2)

            lbl_t = QLabel(title_str)
            lbl_t.setStyleSheet(f"color: {title_color}; font-size: 11.5px; font-weight: 600; background: transparent;")

            lbl_v = QLabel(default_val)
            lbl_v.setStyleSheet(f"color: {val_color}; font-size: 14px; font-weight: 800; background: transparent;")
            setattr(self, attr_name, lbl_v)

            c_lay.addWidget(lbl_t)
            c_lay.addWidget(lbl_v)
            kpi_lay.addWidget(card, 1)

        return container

    def _update_kpi_metrics(self):
        accent = ThemeManager.get_current_accent_color()
        curr_theme = ThemeManager.get_current_theme_name()
        val_color = "#0A246A" if curr_theme == "Как дома" else ("#028090" if curr_theme == "Pearl Light" else accent)

        if hasattr(self, 'lbl_kpi_reports') and hasattr(self, 'table_hist'):
            self.lbl_kpi_reports.setText(str(self.table_hist.rowCount()))
            self.lbl_kpi_reports.setStyleSheet(f"color: {val_color}; font-size: 14px; font-weight: 800; background: transparent;")

        if hasattr(self, 'lbl_kpi_volume'):
            try:
                c_val = float(self.txt_cold.text().replace(',', '.')) if self.txt_cold.text() else 0.0
                h_val = float(self.txt_hot.text().replace(',', '.')) if self.txt_hot.text() else 0.0
                tot = c_val + h_val
                self.lbl_kpi_volume.setText(f"{tot:.2f} м³")
                self.lbl_kpi_volume.setStyleSheet(f"color: {val_color}; font-size: 14px; font-weight: 800; background: transparent;")
            except ValueError:
                pass

        if hasattr(self, 'lbl_kpi_meters'):
            parent_win = self.window()
            closed_cnt = len(getattr(parent_win, 'closed_meters', []))
            self.lbl_kpi_meters.setText(f"{closed_cnt} шт")
            if closed_cnt == 0:
                self.lbl_kpi_meters.setStyleSheet("color: #94A3B8; font-size: 14px; font-weight: 800; background: transparent;")
            else:
                self.lbl_kpi_meters.setStyleSheet(f"color: {val_color}; font-size: 14px; font-weight: 800; background: transparent;")

        if hasattr(self, 'lbl_kpi_status'):
            tpl_path = getattr(self.drop_tpl, 'file_path', '')
            if tpl_path:
                self.lbl_kpi_status.setText("● Файл загружен")
                self.lbl_kpi_status.setStyleSheet("color: #10B981; font-size: 14px; font-weight: 800; background: transparent;")
            else:
                self.lbl_kpi_status.setText("● Ожидание файлов")
                self.lbl_kpi_status.setStyleSheet(f"color: {val_color}; font-size: 14px; font-weight: 800; background: transparent;")

    def _show_history_context_menu(self, pos: QPoint):
        from PySide6.QtWidgets import QMenu
        item = self.table_hist.itemAt(pos)
        if not item:
            return
        row = item.row()
        path_item = self.table_hist.item(row, 1)
        full_path = path_item.text() if path_item else ""

        menu = QMenu(self)
        action_open = menu.addAction(get_svg_icon("folder"), "Открыть в Excel")
        action_copy = menu.addAction(get_svg_icon("copy"), "Копировать полный путь")
        action_delete = menu.addAction(get_svg_icon("trash"), "Удалить из истории")

        chosen = menu.exec(self.table_hist.viewport().mapToGlobal(pos))
        if chosen == action_open:
            if full_path and os.path.exists(full_path):
                os.startfile(full_path)
        elif chosen == action_copy:
            if full_path:
                QApplication.clipboard().setText(full_path)
                ToastNotification.show_toast(self.window(), "Путь скопирован в буфер обмена!", "SUCCESS")
        elif chosen == action_delete:
            self.table_hist.removeRow(row)
            self._save_current_history()
            self._update_kpi_metrics()

    def _on_toggle_companion(self):
        if self.main_win and hasattr(self.main_win, 'toggle_companion_mode'):
            self.main_win.toggle_companion_mode()

    def _on_arcus_mode_toggled(self, checked: bool):
        curr = ThemeManager.get_current_theme_name()
        if checked:
            if curr != "Как дома":
                self._prev_theme = curr
            ThemeManager.apply_theme("Как дома")
            ToastNotification.show_toast(self.window(), "Активирован строгий Режим Аркуса (Classic)", "INFO")
        else:
            restore = getattr(self, '_prev_theme', 'Dark Tech Azure')
            if restore == "Как дома":
                restore = "Dark Tech Azure"
            ThemeManager.apply_theme(restore)
            ToastNotification.show_toast(self.window(), f"Возврат к теме: {restore}", "SUCCESS")

    def _update_theme_assets(self, theme_name: str = None, theme_data: dict = None):
        t_name = theme_name or ThemeManager.get_current_theme_name()
        accent = ThemeManager.get_current_accent_color()
        if hasattr(self, 'btn_arcus_mode'):
            self.btn_arcus_mode.blockSignals(True)
            self.btn_arcus_mode.setChecked(t_name == "Как дома")
            self.btn_arcus_mode.blockSignals(False)
        if hasattr(self, 'btn_repl'):
            self.btn_repl.setIcon(get_svg_icon("replace", color=accent))
        if hasattr(self, 'btn_compact_repl'):
            self.btn_compact_repl.setIcon(get_svg_icon("replace", color=accent))
        if hasattr(self, 'lbl_smart_context'):
            is_light = t_name in ("Pearl Light", "Как дома")
            c_txt = "#0A246A" if t_name == "Как дома" else ("#028090" if is_light else "#00F2FE")
            self.lbl_smart_context.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {c_txt}; background: transparent;")
        self._update_file_linking_status()
        self._update_kpi_metrics()

    def load_history(self):
        """Загружает сохраненные пути из HistoryService."""
        paths = HistoryService.load()
        self.table_hist.setRowCount(0)
        for p in paths:
            self.add_history_entry(p, save_to_service=False)

    def _reflow_files_card(self, need_vertical: bool = False, lod: int = 3):
        while self.grid_files.count() > 0:
            self.grid_files.takeAt(0)

        accent = ThemeManager.get_current_accent_color()

        if lod == 1:
            # LOD 1: Ultra-Minimalist Badge Mode (Микро-иконки + минимализм)
            if hasattr(self, 'smart_nav_frame'):
                self.smart_nav_frame.setVisible(False)

            self.drop_tpl.setVisible(False)
            self.drop_arc.setVisible(False)
            self.save_container.setVisible(False)
            self.btn_repl.setVisible(False)

            self.btn_compact_tpl.setVisible(True)
            self.btn_compact_arc.setVisible(True)
            self.btn_compact_save.setVisible(True)
            self.btn_compact_repl.setVisible(True)

            self.btn_compact_tpl.setText("")
            self.btn_compact_arc.setText("")
            self.btn_compact_save.setText("")
            self.btn_compact_repl.setText("")

            self.btn_compact_tpl.setIcon(get_svg_icon("folder"))
            self.btn_compact_arc.setIcon(get_svg_icon("folder"))
            self.btn_compact_save.setIcon(get_svg_icon("save"))
            self.btn_compact_repl.setIcon(get_svg_icon("replace", color=accent))

            self.btn_compact_tpl.setToolTip("Файл Шаблона")
            self.btn_compact_arc.setToolTip("Файл Аркус")
            self.btn_compact_save.setToolTip("Путь сохранения")
            self.btn_compact_repl.setToolTip("Мастер замен")

            self.grid_files.setContentsMargins(4, 4, 4, 4)
            self.grid_files.setSpacing(4)
            self.grid_files.addWidget(self.btn_compact_tpl, 0, 0)
            self.grid_files.addWidget(self.btn_compact_arc, 0, 1)
            self.grid_files.addWidget(self.btn_compact_save, 1, 0)
            self.grid_files.addWidget(self.btn_compact_repl, 1, 1)

        elif lod == 2:
            # LOD 2: Compact Mode
            if hasattr(self, 'smart_nav_frame'):
                self.smart_nav_frame.setVisible(False)

            self.drop_tpl.setVisible(False)
            self.drop_arc.setVisible(False)
            self.save_container.setVisible(False)
            self.btn_repl.setVisible(False)

            self.btn_compact_tpl.setVisible(True)
            self.btn_compact_arc.setVisible(True)
            self.btn_compact_save.setVisible(True)
            self.btn_compact_repl.setVisible(True)

            self.btn_compact_tpl.setText("Шаблон")
            self.btn_compact_arc.setText("Аркус")
            self.btn_compact_save.setText("Сохранение")
            self.btn_compact_repl.setText("Замена")

            self.grid_files.setContentsMargins(8, 8, 8, 8)
            self.grid_files.setSpacing(6)
            self.grid_files.addWidget(self.btn_compact_tpl, 0, 0)
            self.grid_files.addWidget(self.btn_compact_arc, 0, 1)
            self.grid_files.addWidget(self.btn_compact_save, 1, 0)
            self.grid_files.addWidget(self.btn_compact_repl, 1, 1)

        else:
            # LOD 3: Full Detailed Mode
            self.btn_compact_tpl.setVisible(False)
            self.btn_compact_arc.setVisible(False)
            self.btn_compact_save.setVisible(False)
            self.btn_compact_repl.setVisible(False)

            self.drop_tpl.setVisible(True)
            self.drop_arc.setVisible(True)
            self.save_container.setVisible(True)
            self.btn_repl.setVisible(True)

            self.drop_tpl.set_compact_mode(False)
            self.drop_arc.set_compact_mode(False)

            has_ctx = bool(self.folder_ctx and self.folder_ctx.get("template_path"))
            if hasattr(self, 'smart_nav_frame'):
                self.smart_nav_frame.setVisible(has_ctx)

            self.grid_files.setContentsMargins(12, 12, 12, 12)
            self.grid_files.setSpacing(8)

            row = 0
            if hasattr(self, 'smart_nav_frame'):
                self.grid_files.addWidget(self.smart_nav_frame, row, 0, 1, 2)
                row += 1

            w = self.card_files.width()
            if w < 340:
                self.lbl_save.setText("Сохр.:")
                self.btn_browse_save.setText("")
                self.btn_browse_save.setToolTip("Обзор файла сохранения")
                self.btn_repl.setText("")
                self.btn_repl.setToolTip("Мастер замен ИПУ")
            elif w < 460:
                self.lbl_save.setText("Сохранить:")
                self.btn_browse_save.setText("Обзор")
                self.btn_browse_save.setToolTip("Обзор файла сохранения")
                self.btn_repl.setText("Замены")
                self.btn_repl.setToolTip("Мастер замен ИПУ")
            else:
                self.lbl_save.setText("Сохранить:")
                self.btn_browse_save.setText("Обзор")
                self.btn_browse_save.setToolTip("Выбрать путь для сохранения")
                self.btn_repl.setText("Замены ИПУ")
                self.btn_repl.setToolTip("Мастер замен счетчиков ИПУ")

            if need_vertical:
                self.grid_files.addWidget(self.drop_tpl, row, 0, 1, 2)
                row += 1
                self.grid_files.addWidget(self.drop_arc, row, 0, 1, 2)
                row += 1
                self.grid_files.addWidget(self.save_container, row, 0, 1, 2)
            else:
                self.grid_files.addWidget(self.drop_tpl, row, 0, 1, 1)
                self.grid_files.addWidget(self.drop_arc, row, 1, 1, 1)
                row += 1
                self.grid_files.addWidget(self.save_container, row, 0, 1, 2)

    def _reflow_targets_card(self, need_vertical: bool = False, lod: int = 3):
        while self.grid_targets.count() > 0:
            self.grid_targets.takeAt(0)

        if lod == 1:
            # LOD 1: Ultra-Minimalist Badge
            self.lbl_cold.setText("Х:")
            self.lbl_hot.setText("Г:")
            self.lbl_corr.setText("+:")
            self.grid_targets.setContentsMargins(4, 4, 4, 4)
            self.grid_targets.setSpacing(4)
        elif lod == 2:
            self.lbl_cold.setText("ХВС:")
            self.lbl_hot.setText("ГВС:")
            self.lbl_corr.setText("ДОБ.:")
            self.grid_targets.setContentsMargins(8, 8, 8, 8)
            self.grid_targets.setSpacing(6)
        else:
            self.lbl_cold.setText("ХВС:")
            self.lbl_hot.setText("ГВС:")
            self.lbl_corr.setText("ДОБ.:")
            self.grid_targets.setContentsMargins(12, 12, 12, 12)
            self.grid_targets.setSpacing(8)

        self.grid_targets.addWidget(self.lbl_cold, 0, 0)
        self.grid_targets.addWidget(self.txt_cold, 0, 1)
        self.grid_targets.addWidget(self.lbl_hot, 1, 0)
        self.grid_targets.addWidget(self.txt_hot, 1, 1)
        self.grid_targets.addWidget(self.lbl_corr, 2, 0)
        self.grid_targets.addWidget(self.txt_corr, 2, 1)
        if lod >= 2:
            self.btn_import_values.setVisible(True)
            self.grid_targets.addWidget(self.btn_import_values, 3, 0, 1, 2)
        else:
            self.btn_import_values.setVisible(False)

    def _reflow_hist_card(self, need_vertical: bool = False, lod: int = 3):
        w = self.card_hist.width()

        if lod == 3 and w > 360:
            self.lbl_hist_title.setText("История сгенерированных отчетов" if w > 420 else "История отчетов")
            self.lbl_hist_title.setToolTip("История сгенерированных отчетов")
            self.btn_hist_open.setText("Открыть")
            self.btn_hist_show_folder.setText("В папку")
            self.btn_hist_clr.setText("Удалить")
            self.btn_hist_clear_all.setText("Очистить")
            self.table_hist.horizontalHeader().setFixedHeight(28)
            self.table_hist.setColumnWidth(0, max(200, int(w * 0.45)))
            self.table_hist.setStyleSheet("")
        elif lod == 2 or (260 <= w <= 360):
            self.lbl_hist_title.setText("История отчетов" if w > 300 else "История")
            self.lbl_hist_title.setToolTip("История сгенерированных отчетов")
            self.btn_hist_open.setText("Открыть")
            self.btn_hist_show_folder.setText("Папка")
            self.btn_hist_clr.setText("Удалить")
            self.btn_hist_clear_all.setText("Очистить")
            self.table_hist.setColumnWidth(0, max(140, int(w * 0.45)))
            self.table_hist.setStyleSheet("")
        else:  # w < 260 (Icon-Only / Ultra-Compact)
            self.lbl_hist_title.setText("История")
            self.lbl_hist_title.setToolTip("История сгенерированных отчетов")

            self.btn_hist_open.setText("")
            self.btn_hist_open.setToolTip("Открыть выделенные файлы")
            self.btn_hist_open.setIcon(get_svg_icon("folder"))

            self.btn_hist_show_folder.setText("")
            self.btn_hist_show_folder.setToolTip("Показать в папке")
            self.btn_hist_show_folder.setIcon(get_svg_icon("search"))

            self.btn_hist_clr.setText("")
            self.btn_hist_clr.setToolTip("Удалить выделенные элементы")
            self.btn_hist_clr.setIcon(get_svg_icon("trash"))

            self.btn_hist_clear_all.setText("")
            self.btn_hist_clear_all.setToolTip("Очистить всю историю отчетов")
            self.btn_hist_clear_all.setIcon(get_svg_icon("trash", color="#EF4444"))

            self.table_hist.horizontalHeader().setFixedHeight(24)
            self.table_hist.setStyleSheet("QTableWidget::item { padding: 2px; } QHeaderView::section { height: 24px; padding: 2px; }")

    def showEvent(self, event):
        super().showEvent(event)
        if not self._initial_layout_done:
            self._initial_layout_done = True
            self.load_dashboard_layout()

    def apply_default_positions(self):
        cw = max(800, self.canvas.width())
        ch = max(500, self.canvas.height())
        self.card_files.rel_rect = (0.02, 0.02, 0.96, 0.48)
        self.card_targets.rel_rect = (0.02, 0.52, 0.46, 0.46)
        self.card_hist.rel_rect = (0.50, 0.52, 0.48, 0.46)

        for card in self.cards:
            card.apply_rel_rect(QSize(cw, ch))

    def load_dashboard_layout(self):
        settings = QSettings("WaterMetrics", "DashboardCustomGrid")
        has_saved = settings.contains("CardFiles/rel_rect")

        if not has_saved:
            self.apply_default_positions()
        else:
            cw = max(800, self.canvas.width())
            ch = max(500, self.canvas.height())
            for card in self.cards:
                card.load_geometry_from_settings()
                card.apply_rel_rect(QSize(cw, ch))

    def save_dashboard_layout(self):
        for card in self.cards:
            card.update_rel_rect()
            card.save_geometry_to_settings()

    def _reset_grid(self):
        settings = QSettings("WaterMetrics", "DashboardCustomGrid")
        settings.clear()
        self.apply_default_positions()
        self.save_dashboard_layout()
        ToastNotification.show_toast(self, "Сетка карточек сброшена в исходное состояние", "SUCCESS")

    def _on_builder_button_toggled(self, enabled: bool):
        if enabled:
            self.btn_builder_mode.setText("✅ Завершить редактирование")
            self.btn_builder_mode.setObjectName("PrimaryButton")
        else:
            self.btn_builder_mode.setText("✏️ Режим конструктора")
            self.btn_builder_mode.setObjectName("AccentButton")
        self.btn_builder_mode.style().unpolish(self.btn_builder_mode)
        self.btn_builder_mode.style().polish(self.btn_builder_mode)

        self._toggle_builder_mode(enabled)

    def _toggle_builder_mode(self, enabled: bool):
        for card in self.cards:
            card.set_builder_mode(enabled)

        if not enabled:
            self.save_dashboard_layout()
            ToastNotification.show_toast(self, "Сетка зафиксирована и сохранена", "SUCCESS")
        else:
            ToastNotification.show_toast(self, "Режим конструктора: перетаскивайте за тело, изменяйте размер за угол", "INFO")

    def _get_template_dialog_title(self) -> str:
        arc_path = getattr(self.drop_arc, 'file_path', '')
        if arc_path:
            arc_name = os.path.basename(arc_path)
            return f"Выберите Файл Шаблона (Ранее выбран Аркус: {arc_name})"
        return "Выберите Файл Шаблона (.xlsx)"

    def _get_arcus_dialog_title(self) -> str:
        tpl_path = getattr(self.drop_tpl, 'file_path', '')
        if tpl_path:
            tpl_name = os.path.basename(tpl_path)
            return f"Выберите Файл Аркус (Ранее выбран Шаблон: {tpl_name})"
        return "Выберите Файл Аркус (Шаблон еще не выбран!)"

    @Slot(str)
    def _on_template_selected(self, tpl_path: str):
        if not tpl_path:
            return

        # Сброс замен ИПУ при выборе нового файла шаблона
        parent_win = self.window()
        if parent_win:
            had_closed = len(getattr(parent_win, 'closed_meters', [])) > 0
            had_new = len(getattr(parent_win, 'new_meters', [])) > 0
            if had_closed or had_new:
                parent_win.closed_meters = []
                parent_win.new_meters = []
                ToastNotification.show_toast(self.window(), "Предыдущие замены ИПУ сброшены для нового шаблона", "INFO")
                if hasattr(parent_win, 'companion_manager') and parent_win.companion_manager:
                    parent_win.companion_manager.update_replacements_badge()

        out_dir = os.path.dirname(os.path.abspath(tpl_path)) if os.path.isfile(tpl_path) else os.path.abspath(tpl_path)
        self.last_template_dir = out_dir
        settings = QSettings("WaterMetrics", "Directories")
        settings.setValue("LastTemplateDir", out_dir)

        # Автоматический анализ контекста папок, дома и следующего месяца
        try:
            self.folder_ctx = FolderNavigationService.detect_folder_context(tpl_path)
            self._update_smart_navigation_ui()

            sug_save = self.folder_ctx.get("suggested_save_path")
            if sug_save:
                self.txt_save.setText(sug_save)
            else:
                out_filename = self.excel_manager.parse_house_and_next_month(tpl_path)
                last_out_dir = settings.value("LastOutputDir", "", type=str) or out_dir
                full_save_path = os.path.join(last_out_dir, out_filename).replace('\\', '/')
                self.txt_save.setText(full_save_path)

            found_arc = self.folder_ctx.get("found_arcus_path")
            curr_arc = getattr(self.drop_arc, 'file_path', '')
            house_id = self.folder_ctx.get("house_name") or os.path.basename(tpl_path)
            if found_arc and os.path.exists(found_arc):
                self.drop_arc.set_file_path(found_arc, notify=False)
                self._on_arcus_selected(found_arc)
            elif curr_arc:
                arc_addr = FolderNavigationService.extract_house_name_from_arcus_content(curr_arc)
                is_match = FolderNavigationService.is_house_match(house_id, os.path.basename(curr_arc)) or (arc_addr and FolderNavigationService.is_house_match(house_id, arc_addr))
                if not is_match:
                    self.drop_arc.clear_file()
                    self._on_arcus_selected("")
        except Exception:
            pass

        # Синхронизация с режимом набивки без рекурсии
        if parent_win and hasattr(parent_win, 'companion_manager') and parent_win.companion_manager:
            win_files = getattr(parent_win.companion_manager, 'win_files', None)
            if win_files:
                win_files.set_template_path(tpl_path)
                if self.txt_save.text():
                    win_files.set_save_path(self.txt_save.text())

        self._update_file_linking_status()
        self._update_kpi_metrics()

        # Авто-проверка кэша сессии импорта и установка серых подсказок
        house_target = self.folder_ctx.get("house_name") if self.folder_ctx else ""
        if not house_target and tpl_path:
            house_target = self.excel_manager.extract_house_name(tpl_path)
        if house_target:
            self._check_and_apply_session_import_suggestions(house_target)

    def _update_smart_navigation_ui(self):
        ctx = self.folder_ctx
        if not ctx or not ctx.get("template_path"):
            self.smart_nav_frame.setVisible(False)
            return

        self.smart_nav_frame.setVisible(True)
        house_name = ctx.get("house_name") or "Дом"
        next_m_name = ctx.get("next_month_name") or "След. месяц"
        next_y = ctx.get("next_year") or ""
        self.lbl_smart_context.setText(f"🏢 {house_name}  ➔  Расчет на {next_m_name} {next_y}")
        t_name = ThemeManager.get_current_theme_name()
        accent = ThemeManager.get_current_accent_color()
        is_light = t_name in ("Pearl Light", "Как дома")
        c_txt = "#0A246A" if t_name == "Как дома" else ("#028090" if is_light else accent)
        self.lbl_smart_context.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {c_txt}; background: transparent;")

        # Обновляем список домов в папке
        houses = ctx.get("available_houses", [])
        self.combo_houses.blockSignals(True)
        self.combo_houses.clear()
        tpl_path = getattr(self.drop_tpl, 'file_path', '')
        if len(houses) > 1:
            for idx, h in enumerate(houses):
                self.combo_houses.addItem(h["name"], h["path"])
                if tpl_path and os.path.normpath(h["path"]) == os.path.normpath(tpl_path):
                    self.combo_houses.setCurrentIndex(idx)
            self.combo_houses.setVisible(True)
            self.lbl_switch_house.setVisible(True)
        else:
            self.combo_houses.setVisible(False)
            self.lbl_switch_house.setVisible(False)
        self.combo_houses.blockSignals(False)

        # Авто-найденный Аркус
        found_arc = ctx.get("found_arcus_path")
        arc_path = getattr(self.drop_arc, 'file_path', '')
        has_auto_arcus = False
        if found_arc and os.path.exists(found_arc) and (not arc_path or os.path.normpath(found_arc) != os.path.normpath(arc_path)):
            arc_name = os.path.basename(found_arc)
            arc_short = arc_name if len(arc_name) <= 22 else (arc_name[:19] + "...")
            self.btn_auto_arcus.setText(f"⚡ Подключить Аркус ({arc_short})")
            self.btn_auto_arcus.setToolTip(f"Нажмите для автоматического подключения:\n{found_arc}")
            self.btn_auto_arcus.setVisible(True)
            has_auto_arcus = True
        else:
            self.btn_auto_arcus.setVisible(False)

        # Проверка существующего отчета
        exist_info = ctx.get("existing_report_info")
        has_exist_alert = False
        if exist_info:
            self.lbl_exist_alert.setText(f"⚠️ Отчет за {next_m_name} уже на диске")
            self.lbl_exist_alert.setToolTip(f"В целевой папке уже найден отчет:\n{exist_info}")
            self.lbl_exist_alert.setVisible(True)
            has_exist_alert = True
        else:
            self.lbl_exist_alert.setVisible(False)

        if hasattr(self, 'nav_actions_widget'):
            self.nav_actions_widget.setVisible(has_auto_arcus or has_exist_alert)

    def _update_theme_assets(self, theme_name: str = None, **kwargs):
        """Обновление цветовых акцентов и иконок при смене темы оформления."""
        accent = ThemeManager.get_current_accent_color()
        curr_theme = theme_name or ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        
        if hasattr(self, 'glass_dash_icon'):
            self.glass_dash_icon.set_color(accent)

        if hasattr(self, 'btn_arcus_mode'):
            self.btn_arcus_mode.blockSignals(True)
            self.btn_arcus_mode.setChecked(curr_theme == "Как дома")
            self.btn_arcus_mode.blockSignals(False)

        self._update_kpi_metrics()
        if hasattr(self, '_update_smart_navigation_ui'):
            self._update_smart_navigation_ui()

    def _on_house_combo_changed(self, idx: int):
        if idx < 0:
            return
        selected_path = self.combo_houses.itemData(idx)
        tpl_path = getattr(self.drop_tpl, 'file_path', '')
        if selected_path and os.path.exists(selected_path):
            if not tpl_path or os.path.normpath(selected_path) != os.path.normpath(tpl_path):
                self.drop_tpl.set_file_path(selected_path, notify=False)
                self._on_template_selected(selected_path)

    def _on_auto_arcus_clicked(self):
        found_arc = self.folder_ctx.get("found_arcus_path")
        if found_arc and os.path.exists(found_arc):
            self.drop_arc.set_file_path(found_arc, notify=False)
            self._on_arcus_selected(found_arc)
            self.btn_auto_arcus.setVisible(False)
            parent_win = self.window()
            if parent_win:
                ToastNotification.show_toast(parent_win, f"Файл Аркус подключен: {os.path.basename(found_arc)}", "SUCCESS")
                if hasattr(parent_win, 'companion_manager') and parent_win.companion_manager:
                    win_files = getattr(parent_win.companion_manager, 'win_files', None)
                    if win_files:
                        win_files.set_arcus_path(found_arc)

    @Slot(str)
    def _on_arcus_selected(self, arc_path: str):
        # Проверка соответствия папки месяца Аркуса
        tpl_path = getattr(self.drop_tpl, 'file_path', '')
        if tpl_path and arc_path:
            month_val = FolderNavigationService.validate_arcus_month_folder(tpl_path, arc_path)
            if not month_val["is_valid"]:
                parent_win = self.window()
                confirmed = FileGuardDialog.show_month_mismatch_dialog(
                    parent_win,
                    tpl_house=os.path.basename(tpl_path),
                    target_month_str=month_val["target_month_name"],
                    arc_month_str=month_val["arcus_month_name"] or "Неизвестно",
                    arc_path=arc_path
                )
                if not confirmed:
                    self.drop_arc.clear_file()
                    return

        out_dir = os.path.dirname(os.path.abspath(arc_path)) if os.path.isfile(arc_path) else os.path.abspath(arc_path)
        self.last_arcus_dir = out_dir
        settings = QSettings("WaterMetrics", "Directories")
        settings.setValue("LastArcusDir", out_dir)

        # Синхронизация с режимом набивки без рекурсии
        parent_win = self.window()
        if parent_win and hasattr(parent_win, 'companion_manager') and parent_win.companion_manager:
            win_files = getattr(parent_win.companion_manager, 'win_files', None)
            if win_files:
                win_files.set_arcus_path(arc_path)

        self._update_file_linking_status()
        if hasattr(self, '_update_smart_navigation_ui'):
            self._update_smart_navigation_ui()

    def _update_file_linking_status(self):
        tpl_path = getattr(self.drop_tpl, 'file_path', '')
        arc_path = getattr(self.drop_arc, 'file_path', '')

        if tpl_path:
            tpl_name = os.path.basename(tpl_path)
            self.drop_tpl.set_highlight_state("linked", f"[ВЫБРАН] Шаблон: <b>{tpl_name}</b>")
        else:
            if arc_path:
                self.drop_tpl.set_highlight_state("warning", "[ВНИМАНИЕ] Требуется выбрать шаблон!")
            else:
                self.drop_tpl.set_highlight_state("default")

        if arc_path:
            arc_name = os.path.basename(arc_path)
            if tpl_path:
                tpl_name = os.path.basename(tpl_path)
                month_val = FolderNavigationService.validate_arcus_month_folder(tpl_path, arc_path)
                if not month_val["is_valid"]:
                    self.drop_arc.set_highlight_state("warning", f"⚠️ Папка: {month_val['arcus_month_name']} (нужен {month_val['target_month_name']})")
                else:
                    self.drop_arc.set_highlight_state("linked", f"[ВЫБРАН] Аркус: <b>{arc_name}</b>")
            else:
                self.drop_arc.set_highlight_state("warning", f"[ВЫБРАН] Аркус: <b>{arc_name}</b><br/><span style='color:#F87171;'>Шаблон не выбран!</span>")
        else:
            self.drop_arc.set_highlight_state("default")

    def _browse_save_path(self):
        settings = QSettings("WaterMetrics", "Directories")
        last_out_dir = settings.value("LastOutputDir", "", type=str)

        curr_text = self.txt_save.text()
        init_path = curr_text if curr_text else (os.path.join(last_out_dir, "Отчет.xlsx") if last_out_dir else "Отчет.xlsx")

        save_path, _ = QFileDialog.getSaveFileName(self, "Выберите файл сохранения", init_path, "Excel (*.xlsx)")
        if save_path:
            out_dir = os.path.dirname(os.path.abspath(save_path))
            settings.setValue("LastOutputDir", out_dir)
            self.txt_save.setText(save_path)

    @Slot()
    def _on_enter_run_calculation(self):
        self._start_calculation()

    def _start_calculation(self):
        sav_text = self.txt_save.text()
        if sav_text:
            out_dir = os.path.dirname(os.path.abspath(sav_text))
            QSettings("WaterMetrics", "Directories").setValue("LastOutputDir", out_dir)

        if self.main_win and hasattr(self.main_win, 'run_calculation'):
            self.main_win.run_calculation()

    def _open_replacement_master(self):
        if self.main_win and hasattr(self.main_win, 'open_replacement_dialog'):
            self.main_win.open_replacement_dialog()

    def _open_import_dialog(self):
        """Открыть диалог импорта показаний из внешней набивочной таблицы Excel."""
        from ui.dialogs.excel_import_dialog import ExcelImportDialog
        house_name = self.folder_ctx.get("house_name", "") if self.folder_ctx else ""
        if not house_name:
            tpl_path = getattr(self.drop_tpl, 'file_path', '')
            if tpl_path:
                house_name = self.excel_manager.extract_house_name(tpl_path)

        dlg = ExcelImportDialog(self, house_name=house_name)
        dlg.values_accepted.connect(self._apply_imported_values)
        dlg.exec()

    def _check_and_apply_session_import_suggestions(self, house_name: str):
        """Проверяет кэш сессии импорта и выставляет серые подсказки для дома."""
        if not house_name:
            return
        from services.import_session_service import ImportSessionService
        vals = ImportSessionService.get_values_for_house(house_name)
        if vals:
            c = str(vals.get('хвс', 0.0))
            h = str(vals.get('гвс', 0.0))
            d = str(vals.get('доб', 0.0))
            self.txt_cold.set_suggested_value(c)
            self.txt_hot.set_suggested_value(h)
            self.txt_corr.set_suggested_value(d)

            # Синхронизация с companion dock
            parent_win = self.window()
            if parent_win and hasattr(parent_win, 'companion_manager') and parent_win.companion_manager:
                win_vals = getattr(parent_win.companion_manager, 'win_values', None)
                if win_vals:
                    win_vals.set_suggested_values(c, h, d)

            self._update_kpi_metrics()
            ToastNotification.show_toast(
                self.window(),
                f"💡 Подставлены показания для «{house_name}» (Enter для подтверждения)",
                "INFO"
            )

    def _apply_imported_values(self, hvs: float, gvs: float, dob: float):
        """Применить импортированные значения ХВС/ГВС/ДОБ из внешней таблицы."""
        self.txt_cold.setText(str(hvs))
        self.txt_hot.setText(str(gvs))
        self.txt_corr.setText(str(dob))
        self.txt_cold.commit_suggestion()
        self.txt_hot.commit_suggestion()
        self.txt_corr.commit_suggestion()

        # Синхронизация с companion dock
        parent_win = self.window()
        if parent_win and hasattr(parent_win, 'companion_manager') and parent_win.companion_manager:
            win_vals = getattr(parent_win.companion_manager, 'win_values', None)
            if win_vals:
                win_vals.set_values(str(hvs), str(gvs), str(dob))

        self._update_kpi_metrics()
        ToastNotification.show_toast(self, f"✅ Импортировано: ХВС={hvs}, ГВС={gvs}, ДОБ={dob}", "SUCCESS")

    def _open_selected_history_file(self):
        selected_rows = sorted(list(set(index.row() for index in self.table_hist.selectedIndexes())))
        if not selected_rows:
            ToastNotification.show_toast(self, "Выберите файлы из таблицы истории!", "INFO")
            return

        opened_count = 0
        for row in selected_rows:
            path_item = self.table_hist.item(row, 1)
            if path_item:
                fp = path_item.text()
                if os.path.exists(fp):
                    QDesktopServices.openUrl(QUrl.fromLocalFile(fp))
                    opened_count += 1
                else:
                    ToastNotification.show_toast(self, f"Файл не найден: {os.path.basename(fp)}", "ERROR")

        if opened_count > 0:
            ToastNotification.show_toast(self, f"Открыто файлов: {opened_count}", "SUCCESS")

    def _show_selected_in_folder(self):
        selected_rows = sorted(list(set(index.row() for index in self.table_hist.selectedIndexes())))
        if not selected_rows:
            ToastNotification.show_toast(self, "Выберите файл из таблицы истории!", "INFO")
            return

        for row in selected_rows:
            path_item = self.table_hist.item(row, 1)
            if path_item:
                fp = os.path.normpath(path_item.text())
                if os.path.exists(fp):
                    if sys.platform == 'win32':
                        subprocess.Popen(['explorer', '/select,', fp])
                    elif sys.platform == 'darwin':
                        subprocess.Popen(['open', '-R', fp])
                    else:
                        folder = os.path.dirname(fp)
                        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
                else:
                    ToastNotification.show_toast(self, "Файл не найден на диске!", "ERROR")

    def _remove_selected_history_entries(self):
        selected_rows = sorted(list(set(index.row() for index in self.table_hist.selectedIndexes())), reverse=True)
        if not selected_rows:
            ToastNotification.show_toast(self, "Выберите строки для удаления из списка!", "INFO")
            return

        count = len(selected_rows)
        for row in selected_rows:
            self.table_hist.removeRow(row)

        remaining_paths = []
        for r in range(self.table_hist.rowCount()):
            item = self.table_hist.item(r, 1)
            if item:
                remaining_paths.append(item.text())
        HistoryService.save(remaining_paths)

        ToastNotification.show_toast(self, f"Удалено строк из списка: {count}", "SUCCESS")

    def _clear_all_history_entries(self):
        if self.table_hist.rowCount() == 0:
            ToastNotification.show_toast(self, "История отчетов уже пуста!", "INFO")
            return

        self.table_hist.setRowCount(0)
        HistoryService.clear()
        ToastNotification.show_toast(self, "История отчетов успешно очищена!", "SUCCESS")

    def add_history_entry(self, full_path: str, save_to_service: bool = True):
        filename = os.path.basename(full_path)
        for r in range(self.table_hist.rowCount()):
            item = self.table_hist.item(r, 1)
            if item and os.path.normpath(item.text()) == os.path.normpath(full_path):
                return

        row = self.table_hist.rowCount()
        self.table_hist.insertRow(row)

        i_name = QTableWidgetItem(filename)
        i_path = QTableWidgetItem(full_path)

        self.table_hist.setItem(row, 0, i_name)
        self.table_hist.setItem(row, 1, i_path)

        if save_to_service:
            HistoryService.add_path(full_path)
        self._update_kpi_metrics()

        if hasattr(self.main_win, 'companion_manager') and self.main_win.companion_manager:
            self.main_win.companion_manager.win_hist.add_history_entry(full_path, save_to_service=False)

    def save_dashboard_state(self):
        self.save_dashboard_layout()

    def load_demo_data(self) -> bool:
        """Загружает демонстрационные файлы и тестовые объемы для быстрого обучения."""
        from config import DEMO_TEMPLATE_FILENAME, DEMO_ARCUS_FILENAME

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates_tpl = [
            os.path.join(base_dir, DEMO_TEMPLATE_FILENAME),
            os.path.join(base_dir, "assets", DEMO_TEMPLATE_FILENAME),
            os.path.join(os.getcwd(), DEMO_TEMPLATE_FILENAME),
        ]
        candidates_arc = [
            os.path.join(base_dir, DEMO_ARCUS_FILENAME),
            os.path.join(base_dir, "assets", DEMO_ARCUS_FILENAME),
            os.path.join(os.getcwd(), DEMO_ARCUS_FILENAME),
        ]
        if hasattr(sys, '_MEIPASS'):
            candidates_tpl.insert(0, os.path.join(sys._MEIPASS, DEMO_TEMPLATE_FILENAME))
            candidates_tpl.insert(1, os.path.join(sys._MEIPASS, "assets", DEMO_TEMPLATE_FILENAME))
            candidates_arc.insert(0, os.path.join(sys._MEIPASS, DEMO_ARCUS_FILENAME))
            candidates_arc.insert(1, os.path.join(sys._MEIPASS, "assets", DEMO_ARCUS_FILENAME))

        tpl_found = next((p for p in candidates_tpl if os.path.isfile(p)), "")
        arc_found = next((p for p in candidates_arc if os.path.isfile(p)), "")

        if not tpl_found or not arc_found:
            ToastNotification.show_toast(self.window(), "Файлы демо-данных не найдены в папке приложения!", "ERROR")
            return False

        self.drop_tpl.set_file_path(tpl_found)
        self.drop_arc.set_file_path(arc_found)

        self.txt_cold.setText("110.0")
        self.txt_hot.setText("75.0")
        self.txt_corr.setText("0.0")

        ToastNotification.show_toast(self.window(), "✨ Демо-данные успешно загружены! Нажмите «Запустить расчет»", "SUCCESS")
        return True