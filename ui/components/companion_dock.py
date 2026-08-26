"""
ui/components/companion_dock.py — Премиальный бесшовный режим набивки (WaterMetrics Companion Mode).

Реализует:
1. Единый синхронный выезд ВСЕГО дока при приближении курсора к краю экрана (< 80px / на всю ширину карточек при открытии).
2. Эффект «приближения / приподнимания» (Hover Lift / Zoom) отдельной карточки при наведении мыши на неё.
3. Плавный выезд верхней панели набивки справа/слева из-за экрана.
4. Точный старт карточек из реальных координат дашборда (card_files, card_targets, card_hist, control_panel).
5. 1 секунду демонстрационной паузы в открытом виде перед грациозной парковкой.
6. Перемещение стороны парковки (Справа <-> Слева) с безупречным выездом и отсутствием наездов.
7. Поддержку перетаскивания (Drag & Drop) карточек между собой для изменения их порядка с сохранением в настройках.
8. Надежный возврат в главное окно по кнопке «В окно», F11, Ctrl+D или Escape.
"""

from __future__ import annotations

import os
import sys
from enum import IntEnum, Enum
from typing import List, Optional, Tuple, Dict

from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSizePolicy, QApplication, QBoxLayout
)
from PySide6.QtCore import (
    Qt, QTimer, QPoint, QRect, QSize, Signal, QPropertyAnimation,
    QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup, QEvent,
    QSettings
)
from PySide6.QtGui import (
    QColor, QPainter, QPen, QBrush, QLinearGradient, QCursor,
    QFont, QKeyEvent, QKeySequence, QMouseEvent, QPainterPath
)

from ui.styles import ThemeManager, get_svg_icon
from ui.components.glass_icon import GlassIconWidget
from ui.components.interactive import ExcelDropZone
from ui.components.toast import ToastNotification


class DockSide(Enum):
    RIGHT = "right"
    LEFT = "left"


class CardCategory(IntEnum):
    TOP_BAR = 0
    FILES = 1
    VALUES = 2
    HISTORY = 3
    RUN_PANEL = 4


# ─── БАЗОВОЕ ПАРЯЩЕЕ ОКНО С ЭФФЕКТОМ ПРИБЛИЖЕНИЯ И DRAG & DROP ──────────────────

class EdgeCompanionWindow(QFrame):
    """
    Парящее окно с поддержкой эффекта «приближения» (Hover Lift) при наведении,
    высококонтрастным Frosted Glass фоном, горячими клавишами и Drag & Drop перетаскиванием.
    """

    def __init__(self, category: CardCategory, parent=None):
        super().__init__(parent)
        self.category = category
        self.dock_side = DockSide.RIGHT
        self.manager: Optional[CompanionModeManager] = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setMouseTracking(True)

        self.card_width = 360
        self.parked_peek = 16
        self.is_hovered = False
        self.is_dock_expanded = False
        self.base_docked_x = 0

        # Состояние Drag & Drop
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        self.drag_initial_y = 0
        self._lift_anim = None

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(12, 10, 12, 10)
        self.root_layout.setSpacing(8)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        theme_name = ThemeManager.get_current_theme_name()
        accent = ThemeManager.get_current_accent_color()
        is_light = theme_name in ("Pearl Light", "Как дома")

        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)

        # При наведении или перетаскивании карточка «приближается» — фон становится глубже, свечение ярче
        active = self.is_hovered or self.is_dragging
        if is_light:
            grad = QLinearGradient(0, 0, 0, rect.height())
            grad.setColorAt(0.0, QColor(255, 255, 255, 255))
            grad.setColorAt(1.0, QColor(241, 245, 249, 255 if active else 250))
            border_color = QColor(accent)
            border_color.setAlpha(255 if active else 200)
            glow_pen = QPen(border_color, 2.2 if active else 1.4)
        else:
            grad = QLinearGradient(0, 0, 0, rect.height())
            grad.setColorAt(0.0, QColor(18, 28, 50, 255) if active else QColor(15, 23, 42, 252))
            grad.setColorAt(1.0, QColor(35, 48, 70, 255) if active else QColor(30, 41, 59, 252))
            border_color = QColor(accent)
            border_color.setAlpha(255 if active else 190)
            glow_pen = QPen(border_color, 2.4 if active else 1.4)

        painter.setPen(glow_pen)
        painter.setBrush(QBrush(grad))
        painter.drawPath(path)

    def enterEvent(self, event: QEvent):
        """Эффект приближения: карточка слегка выдвигается вперед на 6px и светится."""
        if not self.manager or not self.manager.is_companion_active:
            try:
                super().enterEvent(event)
            except Exception:
                pass
            return

        self.is_hovered = True
        self.manager.raise_all_cards()
        self.update()

        if self.is_dock_expanded and not self.is_dragging and not self.manager.is_returning_to_window:
            lift_offset = -6 if self.dock_side == DockSide.RIGHT else 6
            target_x = self.base_docked_x + lift_offset
            self._animate_lift(target_x)

        try:
            super().enterEvent(event)
        except Exception:
            pass

    def leaveEvent(self, event: QEvent):
        """Возврат карточки на базовую позицию."""
        if not self.manager or not self.manager.is_companion_active:
            try:
                super().leaveEvent(event)
            except Exception:
                pass
            return

        self.is_hovered = False
        self.update()

        if self.is_dock_expanded and not self.is_dragging and not self.manager.is_returning_to_window:
            self._animate_lift(self.base_docked_x)

        try:
            super().leaveEvent(event)
        except Exception:
            pass

    def _animate_lift(self, target_x: int):
        if self.is_dragging or (self.manager and self.manager.is_returning_to_window):
            return
        if self._lift_anim:
            self._lift_anim.stop()
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(150)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setStartValue(self.geometry())
        anim.setEndValue(QRect(target_x, self.y(), self.card_width, self.height()))
        anim.start()
        self._lift_anim = anim

    def mousePressEvent(self, event: QMouseEvent):
        if not self.manager or not self.manager.is_companion_active:
            super().mousePressEvent(event)
            return

        # Заголовок (панель настроек) не перетаскивается
        if self.category == CardCategory.TOP_BAR:
            super().mousePressEvent(event)
            return

        pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        child = self.childAt(pos)
        is_interactive = isinstance(child, (QLineEdit, QPushButton, QTableWidget, QHeaderView))
        if not is_interactive and event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()
            self.drag_initial_y = self.y()
            self.is_dragging = False
            self.manager.raise_all_cards()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.manager or not self.manager.is_companion_active or self.category == CardCategory.TOP_BAR:
            super().mouseMoveEvent(event)
            return

        if event.buttons() & Qt.MouseButton.LeftButton and not self.drag_start_pos.isNull():
            curr_pos = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()
            delta = curr_pos - self.drag_start_pos
            if not self.is_dragging and abs(delta.y()) > 4:
                self.is_dragging = True
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.manager.on_card_drag_started(self)

            if self.is_dragging:
                screen = QApplication.screenAt(curr_pos) or QApplication.primaryScreen()
                screen_geo = screen.availableGeometry()
                card_h = self.manager._get_card_height(self)
                min_y = screen_geo.top() + 60
                max_y = screen_geo.bottom() - card_h - 10
                new_y = max(min_y, min(max_y, self.drag_initial_y + delta.y()))

                # СТРОГО фиксируем X в док-колонке (карточка не может уехать в центр экрана)
                dock_x = self.manager._get_open_x(screen_geo)
                self.move(dock_x, new_y)
                self.manager.on_card_drag_moved(self, new_y)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.is_dragging:
            self.is_dragging = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.drag_start_pos = QPoint()
            self.update()
            if self.manager:
                self.manager.on_card_drag_ended(self)
            event.accept()
            return
        self.drag_start_pos = QPoint()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        """Обработка горячих клавиш выхода в окно (F11, Ctrl+D, Escape) из любого парящего окна."""
        if event.key() == Qt.Key.Key_F11 or (
            event.key() == Qt.Key.Key_D and (event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        ) or event.key() == Qt.Key.Key_Escape:
            if self.manager:
                self.manager.exit_companion_mode()
            event.accept()
            return
        super().keyPressEvent(event)


# ─── 0. ВЕРХНЯЯ ПАНЕЛЬ НАСТРОЕК (ВЫЕЗЖАЕТ ИЗ-ЗА ЭКРАНА) ─────────────────────────

class CompanionTopSettingsBar(EdgeCompanionWindow):
    """Верхняя управляющая панель с кнопками переключения стороны и возврата."""
    restore_requested = Signal()
    switch_side_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(CardCategory.TOP_BAR, parent)
        self.init_ui()

    def init_ui(self):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        self.lbl_title = QLabel("⚡ Набивка", objectName="FieldLabel")
        accent = ThemeManager.get_current_accent_color()
        self.lbl_title.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {accent};")
        self.lbl_title.setToolTip("Режим набивки WaterMetrics (F11 / Ctrl+D). Карточки можно перетаскивать по порядку.")

        self.btn_side = QPushButton("⇄ Слева", objectName="SecondaryButton")
        self.btn_side.setMinimumHeight(28)
        self.btn_side.setToolTip("Переместить весь стек на противоположный край экрана (Слева / Справа)")
        self.btn_side.clicked.connect(self.switch_side_requested.emit)

        self.btn_restore = QPushButton("⮌ В окно (F11)", objectName="AccentButton")
        self.btn_restore.setMinimumHeight(28)
        self.btn_restore.setToolTip("Вернуться в главное окно программы (F11 / Ctrl+D / Esc)")
        self.btn_restore.clicked.connect(self.restore_requested.emit)

        row.addWidget(self.lbl_title)
        row.addStretch()
        row.addWidget(self.btn_side)
        row.addWidget(self.btn_restore)

        self.root_layout.addLayout(row)


# ─── 1. АУТЕНТИЧНАЯ КАРТОЧКА ФАЙЛОВ (С АДАПТИВНЫМ МОРФИНГОМ) ───────────────────

class AuthenticFilesWindow(EdgeCompanionWindow):
    """Карточка файлов: Шаблон, Аркус, Сохранение, Замена с адаптивным лейаутом при полете."""
    template_changed = Signal(str)
    arcus_changed = Signal(str)
    save_path_changed = Signal(str)
    replacement_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(CardCategory.FILES, parent)
        self.tpl_path = ""
        self.arc_path = ""
        self.save_path = ""
        self.init_ui()

    def init_ui(self):
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(4)
        lbl_hdr = QLabel("⋮⋮  📁 Файлы и настройки", objectName="FieldLabel")
        lbl_hdr.setStyleSheet("font-size: 11px; font-weight: bold; color: #94A3B8;")
        hdr_row.addWidget(lbl_hdr)
        hdr_row.addStretch()
        self.root_layout.addLayout(hdr_row)

        # Контейнер дроп-зон: при широком окне (в дашборде) — горизонтально, в доке — вертикально
        self.drop_box = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        self.drop_box.setSpacing(8)

        self.drop_tpl = ExcelDropZone("Файл Шаблона", "Перетащите файл шаблона")
        self.drop_tpl.setMinimumHeight(48)
        self.drop_tpl.file_dropped.connect(self._on_tpl_dropped)

        self.drop_arc = ExcelDropZone("Файл Аркус", "Перетащите файл Аркус")
        self.drop_arc.setMinimumHeight(48)
        self.drop_arc.file_dropped.connect(self._on_arc_dropped)

        self.drop_box.addWidget(self.drop_tpl)
        self.drop_box.addWidget(self.drop_arc)
        self.root_layout.addLayout(self.drop_box)

        save_box = QHBoxLayout()
        save_box.setSpacing(6)
        lbl_s = QLabel("Сохранить:", objectName="FieldLabel")
        self.txt_save = QLineEdit()
        self.txt_save.setPlaceholderText("Путь к итоговому файлу...")
        self.txt_save.setMinimumHeight(28)
        self.txt_save.textChanged.connect(self.save_path_changed.emit)

        self.btn_browse = QPushButton("Обзор...", objectName="SecondaryButton")
        self.btn_browse.setIcon(get_svg_icon("folder"))
        self.btn_browse.setMinimumHeight(28)
        self.btn_browse.clicked.connect(self._browse_save)

        save_box.addWidget(lbl_s)
        save_box.addWidget(self.txt_save, 1)
        save_box.addWidget(self.btn_browse)
        self.root_layout.addLayout(save_box)

        self.btn_repl = QPushButton("Мастер замен счетчиков", objectName="AccentButton")
        self.btn_repl.setIcon(get_svg_icon("replace"))
        self.btn_repl.setMinimumHeight(28)
        self.btn_repl.clicked.connect(self.replacement_clicked.emit)
        self.root_layout.addWidget(self.btn_repl)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.width() > 500:
            self.drop_box.setDirection(QBoxLayout.Direction.LeftToRight)
        else:
            self.drop_box.setDirection(QBoxLayout.Direction.TopToBottom)

    def _on_tpl_dropped(self, path: str):
        self.tpl_path = path
        self.template_changed.emit(path)

    def _on_arc_dropped(self, path: str):
        self.arc_path = path
        self.arcus_changed.emit(path)

    def set_template_path(self, path: str):
        self.tpl_path = path
        self.drop_tpl.set_file_path(path)

    def set_arcus_path(self, path: str):
        self.arc_path = path
        self.drop_arc.set_file_path(path)

    def set_save_path(self, path: str):
        self.save_path = path
        self.txt_save.setText(path)

    def _browse_save(self):
        from PySide6.QtWidgets import QFileDialog
        f, _ = QFileDialog.getSaveFileName(self, "Сохранить отчет", self.save_path or "", "Excel (*.xlsx)")
        if f:
            self.set_save_path(f)
            self.save_path_changed.emit(f)


# ─── 2. АУТЕНТИЧНАЯ КАРТОЧКА ПОКАЗАТЕЛЕЙ ───────────────────────────────────

class AuthenticValuesWindow(EdgeCompanionWindow):
    """Карточка показателей: ХВС, ГВС, ДОБ., Сумма."""
    values_changed = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(CardCategory.VALUES, parent)
        self.init_ui()

    def init_ui(self):
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(4)
        lbl_hdr = QLabel("⋮⋮  📊 Показатели ввода", objectName="FieldLabel")
        lbl_hdr.setStyleSheet("font-size: 11px; font-weight: bold; color: #94A3B8;")
        hdr_row.addWidget(lbl_hdr)
        hdr_row.addStretch()
        self.root_layout.addLayout(hdr_row)

        grid = QHBoxLayout()
        grid.setSpacing(6)

        self.txt_cold = self._create_input("ХВС:", grid)
        self.txt_hot = self._create_input("ГВС:", grid)
        self.txt_corr = self._create_input("ДОБ.:", grid)

        chain = [self.txt_cold, self.txt_hot, self.txt_corr]
        for field in chain:
            field.linked_fields = chain

        self.root_layout.addLayout(grid)

        self.lbl_sum = QLabel("Сумма: 0.00 м³", objectName="FieldLabel")
        accent = ThemeManager.get_current_accent_color()
        self.lbl_sum.setStyleSheet(f"font-weight: 700; font-size: 12px; color: {accent};")
        self.root_layout.addWidget(self.lbl_sum)

        self.txt_cold.textChanged.connect(self._on_changed)
        self.txt_hot.textChanged.connect(self._on_changed)
        self.txt_corr.textChanged.connect(self._on_changed)

    def _create_input(self, label: str, layout: QHBoxLayout) -> QLineEdit:
        from ui.dashboard_page import SmartNumericLineEdit
        box = QVBoxLayout()
        box.setSpacing(2)
        lbl = QLabel(label, objectName="FieldLabel")
        lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #94A3B8;")
        txt = SmartNumericLineEdit("0.0")
        txt.setMinimumHeight(28)
        box.addWidget(lbl)
        box.addWidget(txt)
        layout.addLayout(box)
        return txt

    def _on_changed(self):
        try:
            c = float(self.txt_cold.text().replace(',', '.') or '0')
            h = float(self.txt_hot.text().replace(',', '.') or '0')
            d = float(self.txt_corr.text().replace(',', '.') or '0')
            self.lbl_sum.setText(f"Сумма: {c + h + d:.2f} м³")
        except Exception:
            self.lbl_sum.setText("Сумма: —")

        self.values_changed.emit(self.txt_cold.text(), self.txt_hot.text(), self.txt_corr.text())

    def set_values(self, c: str, h: str, d: str):
        for field, val in [(self.txt_cold, c), (self.txt_hot, h), (self.txt_corr, d)]:
            field.blockSignals(True)
            field.setText(val or "0.0")
            field.blockSignals(False)
        self._on_changed()


# ─── 3. АУТЕНТИЧНАЯ КАРТОЧКА ИСТОРИИ ───────────────────────────────────────

class AuthenticHistoryWindow(EdgeCompanionWindow):
    """Карточка истории отчетов с таблицей."""

    def __init__(self, parent=None):
        super().__init__(CardCategory.HISTORY, parent)
        self.init_ui()

    def init_ui(self):
        lbl_hist = QLabel("⋮⋮  🕒 История отчетов", objectName="SectionTitle")
        lbl_hist.setStyleSheet("font-size: 11px; font-weight: bold;")
        self.root_layout.addWidget(lbl_hist)

        self.table_hist = QTableWidget(0, 2)
        self.table_hist.setHorizontalHeaderLabels(["Имя файла", "Полный путь"])
        self.table_hist.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_hist.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table_hist.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_hist.verticalHeader().setVisible(False)
        self.table_hist.setMinimumHeight(80)
        self.table_hist.setStyleSheet("""
            QTableWidget {
                background: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 6px;
                color: #FFFFFF;
                font-size: 11px;
            }
        """)
        self.root_layout.addWidget(self.table_hist)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self.btn_open = QPushButton("Открыть", objectName="SecondaryButton")
        self.btn_open.setIcon(get_svg_icon("folder"))
        self.btn_open.setMinimumHeight(26)
        self.btn_open.clicked.connect(self._open_selected)

        self.btn_folder = QPushButton("В папку", objectName="SecondaryButton")
        self.btn_folder.setIcon(get_svg_icon("folder"))
        self.btn_folder.setMinimumHeight(26)
        self.btn_folder.clicked.connect(self._show_in_folder)

        btn_row.addWidget(self.btn_open)
        btn_row.addWidget(self.btn_folder)
        btn_row.addStretch()
        self.root_layout.addLayout(btn_row)

    def sync_from_table(self, source_table: QTableWidget):
        self.table_hist.setRowCount(0)
        for r in range(source_table.rowCount()):
            self.table_hist.insertRow(r)
            item0 = source_table.item(r, 0)
            item1 = source_table.item(r, 1)
            if item0:
                self.table_hist.setItem(r, 0, QTableWidgetItem(item0.text()))
            if item1:
                self.table_hist.setItem(r, 1, QTableWidgetItem(item1.text()))

    def _open_selected(self):
        row = self.table_hist.currentRow()
        if row >= 0:
            item = self.table_hist.item(row, 1)
            if item and os.path.exists(item.text()):
                os.startfile(item.text())

    def _show_in_folder(self):
        row = self.table_hist.currentRow()
        if row >= 0:
            item = self.table_hist.item(row, 1)
            if item and os.path.exists(item.text()):
                from PySide6.QtGui import QDesktopServices
                from PySide6.QtCore import QUrl
                QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(item.text())))


# ─── 4. ОТДЕЛЬНОЕ ОКНО «СФОРМИРОВАТЬ ФАЙЛ ОТЧЕТА» ─────────────────────────

class AuthenticRunWindow(EdgeCompanionWindow):
    """Отдельное окно с большой кнопкой расчета (стартует из control_panel)."""
    run_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(CardCategory.RUN_PANEL, parent)
        self.init_ui()

    def init_ui(self):
        self.btn_run = QPushButton("⚡ Сформировать файл отчета", objectName="PrimaryButton")
        self.btn_run.setIcon(get_svg_icon("run", color="#020617"))
        self.btn_run.setMinimumHeight(38)
        self.btn_run.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run.clicked.connect(self.run_requested.emit)
        self.root_layout.addWidget(self.btn_run)


# ─── 5. ГЛАВНЫЙ МЕНЕДЖЕР РЕЖИМА НАБИВКИ (COMPANION DOCK MANAGER) ───────────────

class CompanionModeManager:
    """
    Бесшовный координатор режима набивки:
    1. Единый синхронный выезд ВСЕГО дока при приближении мыши.
    2. Эффект приближения (Hover Lift) конкретной карточки при наведении.
    3. Выезд верхней панели набивки справа/слева из-за экрана.
    4. Точный старт из 4 элементов дашборда с динамическим морфингом размеров.
    5. Поддержка Drag & Drop изменения порядка карточек строго в пределах док-колонки.
    6. 100% надежный возврат в главное окно.
    """

    def __init__(self, main_win):
        self.main_win = main_win
        self.is_companion_active = False
        self.is_returning_to_window = False
        self.saved_main_geometry = QRect()
        self.saved_main_is_maximized = False
        self.saved_card_geometries: Dict[CardCategory, QRect] = {}
        self.dock_side = DockSide.RIGHT

        self.win_top_bar = CompanionTopSettingsBar()
        self.win_files = AuthenticFilesWindow()
        self.win_values = AuthenticValuesWindow()
        self.win_hist = AuthenticHistoryWindow()
        self.win_run = AuthenticRunWindow()

        # Единый список всех 5 окон в строгом вертикальном порядке (Top Bar всегда на индексе 0)
        self.cards: List[EdgeCompanionWindow] = [
            self.win_top_bar,
            self.win_files,
            self.win_values,
            self.win_hist,
            self.win_run
        ]

        for card in self.cards:
            card.manager = self

        self.card_heights: Dict[EdgeCompanionWindow, int] = {
            self.win_top_bar: 46,
            self.win_files: 230,
            self.win_values: 120,
            self.win_hist: 185,
            self.win_run: 60,
        }
        self.card_spacing = 10
        self.dock_width = 360
        self.parked_peek = 16
        self.is_dock_expanded = False
        self._animating_dock = False
        self._active_anim_group = None

        self.proximity_timer = QTimer()
        self.proximity_timer.setInterval(30)
        self.proximity_timer.timeout.connect(self._check_dock_proximity)

        self.leave_timer = QTimer()
        self.leave_timer.setSingleShot(True)
        self.leave_timer.setInterval(500)
        self.leave_timer.timeout.connect(self._collapse_dock_together)

        self._load_settings()
        self._connect_signals()
        ThemeManager.on_theme_changed.append(self.update_theme_styles)

    def raise_all_cards(self):
        """Поднимает все карточки режима набивки поверх других приложений (Excel/1C)."""
        for card in self.cards:
            card.raise_()

    def _connect_signals(self):
        self.win_top_bar.restore_requested.connect(self.exit_companion_mode)
        self.win_top_bar.switch_side_requested.connect(self.toggle_dock_side)

        self.win_files.template_changed.connect(self._sync_tpl_to_main)
        self.win_files.arcus_changed.connect(self._sync_arc_to_main)
        self.win_files.save_path_changed.connect(self._sync_save_to_main)
        self.win_files.replacement_clicked.connect(
            lambda: self.main_win.open_replacement_dialog() if hasattr(self.main_win, 'open_replacement_dialog') else None
        )
        self.win_values.values_changed.connect(self._sync_values_to_main)
        self.win_run.run_requested.connect(self._run_calculation)

    def _load_settings(self):
        """Загрузка настроек стороны дока и порядка карточек."""
        settings = QSettings("WaterMetrics", "WaterMetricsApp")
        side_val = settings.value("companion/dock_side", "right")
        self.dock_side = DockSide.LEFT if side_val == "left" else DockSide.RIGHT
        self.win_top_bar.btn_side.setText("⇄ Справа" if self.dock_side == DockSide.LEFT else "⇄ Слева")
        for card in self.cards:
            card.dock_side = self.dock_side

        saved_order = settings.value("companion/card_order", None)
        if saved_order and isinstance(saved_order, list):
            content_map = {
                CardCategory.FILES.value: self.win_files,
                CardCategory.VALUES.value: self.win_values,
                CardCategory.HISTORY.value: self.win_hist,
                CardCategory.RUN_PANEL.value: self.win_run,
            }
            ordered = []
            for cat_val in saved_order:
                try:
                    c_int = int(cat_val)
                    if c_int in content_map and content_map[c_int] not in ordered:
                        ordered.append(content_map[c_int])
                except (ValueError, TypeError):
                    pass
            for c in [self.win_files, self.win_values, self.win_hist, self.win_run]:
                if c not in ordered:
                    ordered.append(c)
            self.cards = [self.win_top_bar] + ordered
        else:
            self.cards = [self.win_top_bar, self.win_files, self.win_values, self.win_hist, self.win_run]

    def _save_card_order(self):
        """Сохранение порядка контентных карточек."""
        settings = QSettings("WaterMetrics", "WaterMetricsApp")
        order_list = [c.category.value for c in self.cards if c is not self.win_top_bar]
        settings.setValue("companion/card_order", order_list)

    def update_theme_styles(self, theme_name: str = None):
        for win in self.cards:
            win.update()

    def _get_card_height(self, card: EdgeCompanionWindow) -> int:
        base_h = self.card_heights.get(card, 60)
        hint_h = card.sizeHint().height()
        return max(base_h, hint_h)

    def _get_open_x(self, screen_geo: QRect) -> int:
        if self.dock_side == DockSide.LEFT:
            return screen_geo.left() + 6
        else:
            return screen_geo.right() - self.dock_width - 6

    def _get_park_x(self, screen_geo: QRect) -> int:
        if self.dock_side == DockSide.LEFT:
            return screen_geo.left() - (self.dock_width - self.parked_peek)
        else:
            return screen_geo.right() - self.parked_peek

    def toggle_dock_side(self):
        """Переключение стороны парковки (Справа <-> Слева). Все 5 окон переезжают абсолютно синхронно."""
        if self._active_anim_group:
            self._active_anim_group.stop()

        self.dock_side = DockSide.LEFT if self.dock_side == DockSide.RIGHT else DockSide.RIGHT
        settings = QSettings("WaterMetrics", "WaterMetricsApp")
        settings.setValue("companion/dock_side", self.dock_side.value)

        side_text = "Слева" if self.dock_side == DockSide.LEFT else "Справа"
        self.win_top_bar.btn_side.setText("⇄ Справа" if self.dock_side == DockSide.LEFT else "⇄ Слева")

        for card in self.cards:
            card.dock_side = self.dock_side

        screen = QApplication.screenAt(self.cards[0].pos()) or QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        target_positions = self._calculate_dock_positions(screen_geo)

        open_x = self._get_open_x(screen_geo)
        park_x = self._get_park_x(screen_geo)
        target_x = open_x if self.is_dock_expanded else park_x

        group = QParallelAnimationGroup()
        for card in self.cards:
            target_y = target_positions[card]
            h = self._get_card_height(card)
            card.base_docked_x = open_x

            anim = QPropertyAnimation(card, b"geometry")
            anim.setDuration(350)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.setStartValue(card.geometry())
            anim.setEndValue(QRect(target_x, target_y, self.dock_width, h))
            group.addAnimation(anim)

        def on_toggle_done():
            self.raise_all_cards()
            self._check_dock_proximity()

        group.finished.connect(on_toggle_done)
        self._active_anim_group = group
        group.start()
        if isinstance(self.main_win, QWidget):
            ToastNotification.show_toast(self.main_win, f"Панели перемещены {side_text.lower()}", "INFO")

    def enter_companion_mode(self):
        """Бесшовный старт: окна появляются ровно в координатах дашборда и плавно летят к краю, трансформируя размеры."""
        if self.is_companion_active:
            return

        if self._active_anim_group:
            self._active_anim_group.stop()

        self.is_companion_active = True
        self.is_returning_to_window = False
        self.saved_main_is_maximized = self.main_win.isMaximized()
        self.saved_main_geometry = self.main_win.geometry()

        p_main = getattr(self.main_win, 'page_main', None)
        if p_main:
            self.win_files.set_template_path(p_main.drop_tpl.file_path)
            self.win_files.set_arcus_path(p_main.drop_arc.file_path)
            self.win_files.set_save_path(p_main.txt_save.text())
            self.win_values.set_values(p_main.txt_cold.text(), p_main.txt_hot.text(), p_main.txt_corr.text())
            if hasattr(p_main, 'table_hist'):
                self.win_hist.sync_from_table(p_main.table_hist)

        self.saved_card_geometries = self._read_dashboard_geometries()

        screen = QApplication.screenAt(self.main_win.pos()) or QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        target_positions = self._calculate_dock_positions(screen_geo)
        open_x = self._get_open_x(screen_geo)

        # 1. Синхронизируем сторону и кнопку
        self.win_top_bar.btn_side.setText("⇄ Справа" if self.dock_side == DockSide.LEFT else "⇄ Слева")
        for card in self.cards:
            card.dock_side = self.dock_side

        # 2. Начальное положение верхней панели: появляется сверху в док-колонке и опускается
        start_top_y = screen_geo.top() - 60
        self.win_top_bar.setGeometry(QRect(open_x, start_top_y, self.dock_width, self._get_card_height(self.win_top_bar)))
        self.win_top_bar.show()

        # 3. Контентные карточки появляются РОВНО на месте и в РАЗМЕРАХ карточек дашборда (Image 2 -> Image 3)
        mapping = [
            (self.win_files, CardCategory.FILES),
            (self.win_values, CardCategory.VALUES),
            (self.win_hist, CardCategory.HISTORY),
            (self.win_run, CardCategory.RUN_PANEL)
        ]

        fallback_geo = self.saved_main_geometry if (self.saved_main_geometry.isValid() and not self.saved_main_geometry.isEmpty()) else QRect(100, 100, 600, 400)
        for card, cat in mapping:
            start_geo = self.saved_card_geometries.get(cat, fallback_geo)
            card.setGeometry(start_geo)
            card.show()

        self.raise_all_cards()

        # 4. Скрываем главное окно
        self.main_win.hide()

        # 5. Плавная морфинг-анимация полета ВСЕХ 5 окон к док-колонке (Image 3 -> Image 4)
        group = QParallelAnimationGroup()

        for i, card in enumerate(self.cards):
            target_y = target_positions[card]
            h = self._get_card_height(card)

            card.base_docked_x = open_x
            card.is_dock_expanded = True
            open_geo = QRect(open_x, target_y, self.dock_width, h)

            delay = i * 35
            anim = QPropertyAnimation(card, b"geometry")
            anim.setDuration(560)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            anim.setStartValue(card.geometry())
            anim.setEndValue(open_geo)

            if delay > 0:
                seq = QSequentialAnimationGroup()
                seq.addPause(delay)
                seq.addAnimation(anim)
                group.addAnimation(seq)
            else:
                group.addAnimation(anim)

        def on_open_flight_done():
            self.raise_all_cards()
            # Оставляем открытыми на 1 СЕКУНДУ (1000 мс) перед грациозной парковкой
            QTimer.singleShot(1000, self._park_all_cards_together)

        group.finished.connect(on_open_flight_done)
        self._active_anim_group = group
        group.start()

    def _park_all_cards_together(self):
        """Парковка всех 5 окон ЗА край экрана вместе."""
        if not self.is_companion_active or self.is_returning_to_window:
            return

        if self._active_anim_group:
            self._active_anim_group.stop()

        screen = QApplication.screenAt(self.cards[0].pos()) or QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        target_positions = self._calculate_dock_positions(screen_geo)
        park_x = self._get_park_x(screen_geo)

        group = QParallelAnimationGroup()
        for card in self.cards:
            target_y = target_positions[card]
            h = self._get_card_height(card)

            card.is_dock_expanded = False
            anim = QPropertyAnimation(card, b"geometry")
            anim.setDuration(400)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.setStartValue(card.geometry())
            anim.setEndValue(QRect(park_x, target_y, self.dock_width, h))
            group.addAnimation(anim)

        def on_park_done():
            self.is_dock_expanded = False
            self.proximity_timer.start()
            self.raise_all_cards()

        group.finished.connect(on_park_done)
        self._active_anim_group = group
        group.start()

    def _check_dock_proximity(self):
        """Проверка приближения/ухода мыши: единый выезд и сворачивание дока."""
        if not self.is_companion_active or self.is_returning_to_window or self._animating_dock:
            return
        if any(c.is_dragging for c in self.cards):
            return

        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos) or QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()

        target_positions = self._calculate_dock_positions(screen_geo)
        top_y = min(target_positions.values()) - 30
        bottom_y = max(target_positions[c] + self._get_card_height(c) for c in self.cards) + 30
        is_in_y = top_y <= cursor_pos.y() <= bottom_y

        if self.dock_side == DockSide.RIGHT:
            if self.is_dock_expanded:
                is_in_dock_zone = (cursor_pos.x() >= (screen_geo.right() - self.dock_width - 40)) and is_in_y
            else:
                is_in_dock_zone = (cursor_pos.x() >= (screen_geo.right() - 80)) and is_in_y
        else:
            # ЛЕВАЯ СТОРОНА
            if self.is_dock_expanded:
                is_in_dock_zone = (cursor_pos.x() <= (screen_geo.left() + self.dock_width + 40)) and is_in_y
            else:
                is_in_dock_zone = (cursor_pos.x() <= (screen_geo.left() + 80)) and is_in_y

        # Проверка нахождения курсора над карточками текущей стороны
        is_over_card = any(
            c.geometry().contains(cursor_pos)
            for c in self.cards
            if (self.dock_side == DockSide.LEFT and c.x() < screen_geo.center().x()) or
               (self.dock_side == DockSide.RIGHT and c.x() > screen_geo.center().x())
        )

        if is_in_dock_zone or is_over_card:
            self.leave_timer.stop()
            if not self.is_dock_expanded:
                self._expand_dock_together()
        else:
            if self.is_dock_expanded and not self.leave_timer.isActive():
                self.leave_timer.start()

    def _expand_dock_together(self):
        """Единый синхронный выезд ВСЕГО дока при приближении мыши."""
        if not self.is_companion_active or self.is_returning_to_window:
            return

        if self._active_anim_group:
            self._active_anim_group.stop()

        self._animating_dock = True
        screen = QApplication.screenAt(self.cards[0].pos()) or QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        target_positions = self._calculate_dock_positions(screen_geo)
        open_x = self._get_open_x(screen_geo)

        group = QParallelAnimationGroup()
        for card in self.cards:
            target_y = target_positions[card]
            h = self._get_card_height(card)

            card.base_docked_x = open_x
            anim = QPropertyAnimation(card, b"geometry")
            anim.setDuration(240)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.setStartValue(card.geometry())
            anim.setEndValue(QRect(open_x, target_y, self.dock_width, h))
            group.addAnimation(anim)

        def on_expand_done():
            self._animating_dock = False
            self.is_dock_expanded = True
            for c in self.cards:
                c.is_dock_expanded = True
            self.raise_all_cards()

        group.finished.connect(on_expand_done)
        self._active_anim_group = group
        group.start()

    def _collapse_dock_together(self):
        """Единый синхронный уезд ВСЕГО дока за край экрана."""
        if not self.is_companion_active or self.is_returning_to_window:
            return
        if any(c.is_dragging for c in self.cards):
            return

        if self._active_anim_group:
            self._active_anim_group.stop()

        self._animating_dock = True
        screen = QApplication.screenAt(self.cards[0].pos()) or QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        target_positions = self._calculate_dock_positions(screen_geo)
        park_x = self._get_park_x(screen_geo)

        group = QParallelAnimationGroup()
        for card in self.cards:
            target_y = target_positions[card]
            h = self._get_card_height(card)

            anim = QPropertyAnimation(card, b"geometry")
            anim.setDuration(240)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.setStartValue(card.geometry())
            anim.setEndValue(QRect(park_x, target_y, self.dock_width, h))
            group.addAnimation(anim)

        def on_collapse_done():
            self._animating_dock = False
            self.is_dock_expanded = False
            for c in self.cards:
                c.is_dock_expanded = False
            self.raise_all_cards()

        group.finished.connect(on_collapse_done)
        self._active_anim_group = group
        group.start()

    # ─── DRAG & DROP REORDERING (СТРОГО В ПРЕДЕЛАХ ДОК-КОЛОНКИ) ───────────

    def on_card_drag_started(self, dragged_card: EdgeCompanionWindow):
        if dragged_card is self.win_top_bar:
            return
        self.proximity_timer.stop()
        self.leave_timer.stop()
        self.raise_all_cards()
        dragged_card.raise_()

    def on_card_drag_moved(self, dragged_card: EdgeCompanionWindow, current_y: int):
        if dragged_card is self.win_top_bar:
            return

        screen = QApplication.screenAt(dragged_card.pos()) or QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()

        dragged_center_y = current_y + self._get_card_height(dragged_card) / 2
        cur_idx = self.cards.index(dragged_card)
        target_idx = cur_idx

        # Перемещение вверх через карточки (не выше top_bar, то есть target_idx >= 1)
        while target_idx > 1:
            prev_card = self.cards[target_idx - 1]
            prev_center_y = prev_card.y() + self._get_card_height(prev_card) / 2
            if dragged_center_y < prev_center_y:
                target_idx -= 1
            else:
                break

        # Перемещение вниз через карточки
        while target_idx < len(self.cards) - 1:
            next_card = self.cards[target_idx + 1]
            next_center_y = next_card.y() + self._get_card_height(next_card) / 2
            if dragged_center_y > next_center_y:
                target_idx += 1
            else:
                break

        if target_idx != cur_idx:
            self.cards.remove(dragged_card)
            self.cards.insert(target_idx, dragged_card)
            self._realign_other_cards(dragged_card, screen_geo)

    def _realign_other_cards(self, dragged_card: EdgeCompanionWindow, screen_geo: QRect):
        target_positions = self._calculate_dock_positions(screen_geo)
        open_x = self._get_open_x(screen_geo)
        for card in self.cards:
            if card is not dragged_card:
                target_y = target_positions[card]
                if card.y() != target_y or card.x() != open_x:
                    anim = QPropertyAnimation(card, b"geometry")
                    anim.setDuration(160)
                    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                    anim.setStartValue(card.geometry())
                    anim.setEndValue(QRect(open_x, target_y, self.dock_width, self._get_card_height(card)))
                    anim.start()
                    card._lift_anim = anim

    def on_card_drag_ended(self, dragged_card: EdgeCompanionWindow):
        if dragged_card is self.win_top_bar:
            return

        screen = QApplication.screenAt(dragged_card.pos()) or QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        target_positions = self._calculate_dock_positions(screen_geo)

        target_y = target_positions[dragged_card]
        open_x = self._get_open_x(screen_geo)
        h = self._get_card_height(dragged_card)

        anim = QPropertyAnimation(dragged_card, b"geometry")
        anim.setDuration(200)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setStartValue(dragged_card.geometry())
        anim.setEndValue(QRect(open_x, target_y, self.dock_width, h))
        anim.start()
        dragged_card._lift_anim = anim

        self._save_card_order()
        self.proximity_timer.start()
        self.raise_all_cards()

    # ─── ВЫХОД В ОКНО (С ОБРАТНЫМ МОРФИНГОМ) ──────────────────────────────

    def exit_companion_mode(self):
        """Бесшовный обратный полет карточек с морфингом размеров и надежное восстановление главного окна."""
        if not self.is_companion_active or self.is_returning_to_window:
            return

        self.is_companion_active = False
        self.is_returning_to_window = True
        self.proximity_timer.stop()
        self.leave_timer.stop()

        if self._active_anim_group:
            self._active_anim_group.stop()

        for card in self.cards:
            card.is_dock_expanded = False
            card.is_hovered = False
            card.is_dragging = False
            if hasattr(card, '_lift_anim') and card._lift_anim:
                card._lift_anim.stop()

        # Синхронизация данных обратно
        p_main = getattr(self.main_win, 'page_main', None)
        if p_main:
            self._sync_tpl_to_main(self.win_files.tpl_path)
            self._sync_arc_to_main(self.win_files.arc_path)
            self._sync_save_to_main(self.win_files.txt_save.text())
            self._sync_values_to_main(
                self.win_values.txt_cold.text(),
                self.win_values.txt_hot.text(),
                self.win_values.txt_corr.text()
            )

        def restore_main_window():
            for card in self.cards:
                card.hide()

            self.main_win.show()
            if getattr(self, 'saved_main_is_maximized', False):
                self.main_win.showMaximized()
            else:
                if self.saved_main_geometry.isValid() and not self.saved_main_geometry.isEmpty():
                    self.main_win.setGeometry(self.saved_main_geometry)
                self.main_win.showNormal()

            self.main_win.raise_()
            self.main_win.activateWindow()
            self.is_returning_to_window = False
            if isinstance(self.main_win, QWidget):
                ToastNotification.show_toast(self.main_win, "Главное окно восстановлено", "INFO")

        # Анимация полета обратно: карточки расширяются обратно в размеры дашборда
        group = QParallelAnimationGroup()

        mapping = [
            (self.win_files, CardCategory.FILES),
            (self.win_values, CardCategory.VALUES),
            (self.win_hist, CardCategory.HISTORY),
            (self.win_run, CardCategory.RUN_PANEL)
        ]

        for i, (card, cat) in enumerate(mapping):
            target_geo = self.saved_card_geometries.get(cat, self.saved_main_geometry)
            if not target_geo.isValid() or target_geo.isEmpty():
                target_geo = self.saved_main_geometry

            anim = QPropertyAnimation(card, b"geometry")
            anim.setDuration(460)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            anim.setStartValue(card.geometry())
            anim.setEndValue(target_geo)

            delay = (3 - i) * 35
            if delay > 0:
                seq = QSequentialAnimationGroup()
                seq.addPause(delay)
                seq.addAnimation(anim)
                group.addAnimation(seq)
            else:
                group.addAnimation(anim)

        screen = QApplication.screenAt(self.win_top_bar.pos()) or QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        anim_top = QPropertyAnimation(self.win_top_bar, b"geometry")
        anim_top.setDuration(350)
        anim_top.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_top.setStartValue(self.win_top_bar.geometry())
        anim_top.setEndValue(QRect(self.win_top_bar.x(), screen_geo.top() - 60, self.dock_width, self._get_card_height(self.win_top_bar)))
        group.addAnimation(anim_top)

        # Страховочный таймер: если по какой-то причине finished не сработал за 550мс, окно все равно откроется
        self._restore_fallback_timer = QTimer()
        self._restore_fallback_timer.setSingleShot(True)
        self._restore_fallback_timer.timeout.connect(restore_main_window)
        self._restore_fallback_timer.start(550)

        def on_finished():
            if hasattr(self, '_restore_fallback_timer'):
                self._restore_fallback_timer.stop()
            restore_main_window()

        group.finished.connect(on_finished)
        self._active_anim_group = group
        group.start()

    def _read_dashboard_geometries(self) -> Dict[CardCategory, QRect]:
        geoms = {}
        p_main = getattr(self.main_win, 'page_main', None)
        if not p_main:
            return geoms

        if hasattr(p_main, 'card_files') and p_main.card_files.isVisible():
            g_pos = p_main.card_files.mapToGlobal(QPoint(0, 0))
            geoms[CardCategory.FILES] = QRect(g_pos, p_main.card_files.size())

        if hasattr(p_main, 'card_targets') and p_main.card_targets.isVisible():
            g_pos = p_main.card_targets.mapToGlobal(QPoint(0, 0))
            geoms[CardCategory.VALUES] = QRect(g_pos, p_main.card_targets.size())

        if hasattr(p_main, 'card_hist') and p_main.card_hist.isVisible():
            g_pos = p_main.card_hist.mapToGlobal(QPoint(0, 0))
            geoms[CardCategory.HISTORY] = QRect(g_pos, p_main.card_hist.size())

        if hasattr(p_main, 'control_panel') and p_main.control_panel.isVisible():
            g_pos = p_main.control_panel.mapToGlobal(QPoint(0, 0))
            geoms[CardCategory.RUN_PANEL] = QRect(g_pos, p_main.control_panel.size())
        else:
            geoms[CardCategory.RUN_PANEL] = QRect(self.main_win.x(), self.main_win.y() + self.main_win.height() - 60, self.main_win.width(), 50)

        return geoms

    def _calculate_dock_positions(self, screen_geo: QRect) -> Dict[EdgeCompanionWindow, int]:
        total_h = sum(self._get_card_height(c) for c in self.cards) + (len(self.cards) - 1) * self.card_spacing
        start_y = screen_geo.top() + max(12, int((screen_geo.height() - total_h) / 2))

        cur_y = start_y
        positions = {}
        for card in self.cards:
            positions[card] = cur_y
            cur_y += self._get_card_height(card) + self.card_spacing
        return positions

    # ─── Синхронизация данных ─────────────────────────────────────────────

    def _sync_tpl_to_main(self, path: str):
        p_main = getattr(self.main_win, 'page_main', None)
        if p_main and hasattr(p_main, 'drop_tpl'):
            p_main.drop_tpl.set_file_path(path)
            if hasattr(p_main, '_on_template_selected'):
                p_main._on_template_selected(path)

    def _sync_arc_to_main(self, path: str):
        p_main = getattr(self.main_win, 'page_main', None)
        if p_main and hasattr(p_main, 'drop_arc'):
            p_main.drop_arc.set_file_path(path)
            if hasattr(p_main, '_on_arcus_selected'):
                p_main._on_arcus_selected(path)

    def _sync_values_to_main(self, cold: str, hot: str, corr: str):
        p_main = getattr(self.main_win, 'page_main', None)
        if p_main:
            for attr, val in [('txt_cold', cold), ('txt_hot', hot), ('txt_corr', corr)]:
                if hasattr(p_main, attr):
                    field = getattr(p_main, attr)
                    if field.text() != val:
                        field.blockSignals(True)
                        field.setText(val)
                        field.blockSignals(False)

    def _sync_save_to_main(self, path: str):
        p_main = getattr(self.main_win, 'page_main', None)
        if p_main and hasattr(p_main, 'txt_save'):
            p_main.txt_save.setText(path)

    def _run_calculation(self):
        if hasattr(self.main_win, 'run_calculation'):
            self.win_run.btn_run.setEnabled(False)
            self.main_win.run_calculation()
            QTimer.singleShot(1800, lambda: self.win_run.btn_run.setEnabled(True))
