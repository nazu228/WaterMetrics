"""
ui/components/companion_dock.py — Премиальный бесшовный режим набивки (WaterMetrics Companion Mode).

Реализует:
1. Полную блокировку взаимодействия с окнами во время всех анимаций перемещения (полет в док, парковка, выезд, смена стороны, возврат).
2. Разблокировку и 100% интерактивность сразу после завершения полета (включая демонстрационную 1-секундную паузу и режим раскрытого дока).
3. 100% сохранение ВСЕХ функций дашборда:
   - Мастер замен счетчиков (набитие новых ИПУ) с бейджами и синхронизацией.
   - Запоминание и выбор директорий (LastTemplateDir, LastArcusDir, LastOutputDir) с информативными заголовками диалогов.
   - Надежное открытие файлов по клику на дроп-зоны (Шаблон, Аркус) и открытие отчетов в Excel по двойному клику / кнопке.
   - Автоматический расчет имени файла следующего месяца при выборе шаблона.
   - Подсветка связи файлов (связано / внимание / по умолчанию).
   - Умный ввод показателей с поддержкой множественной вставки из Excel (Ctrl+V) и цепочкой Enter.
   - Полнофункциональная история с идеальной подгонкой размеров (без обрезаний и выпираний), контекстным меню, кнопками удаления и очистки.
   - Запуск расчета с индикацией прогресса, анти-спам дебаунсом и Toast-уведомлениями прямо поверх Excel/1C.
4. Единый синхронный и стабильный выезд ВСЕГО дока при приближении курсора к краю экрана (< 85px).
5. Эффект «Hover Lift / Zoom» отдельной карточки при наведении мыши.
6. Двусторонняя парковка (Справа <-> Слева) с сохранением в QSettings.
7. Вертикальная перестановка карточек (Drag & Drop) строго внутри док-колонки с сохранением порядка в QSettings.
8. Надежный и бесшовный обратный полет карточек в дашборд (F11 / Ctrl+D / Esc).
"""

from __future__ import annotations

import os
import sys
import subprocess
from enum import IntEnum, Enum
from typing import List, Optional, Tuple, Dict

from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSizePolicy, QApplication, QBoxLayout, QMenu,
    QDialog, QFileDialog
)
from PySide6.QtCore import (
    Qt, QTimer, QPoint, QRect, QSize, Signal, Slot, QPropertyAnimation,
    QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup, QEvent,
    QSettings, QUrl
)
from PySide6.QtGui import (
    QColor, QPainter, QPen, QBrush, QLinearGradient, QCursor,
    QFont, QKeyEvent, QKeySequence, QMouseEvent, QPainterPath, QDesktopServices
)

from core.excel_parser import ExcelManager
from services.history_service import HistoryService
from ui.styles import ThemeManager, get_svg_icon
from ui.components.glass_icon import GlassIconWidget
from ui.components.interactive import ExcelDropZone
from ui.components.toast import ToastNotification
from ui.dialogs.replacement_dialog import MeterReplacementDialog
from ui.dashboard_page import SmartNumericLineEdit


class DockSide(Enum):
    RIGHT = "right"
    LEFT = "left"


class CardCategory(IntEnum):
    TOP_BAR = 0
    FILES = 1
    VALUES = 2
    HISTORY = 3
    RUN_PANEL = 4


# ─── БАЗОВОЕ ПАРЯЩЕЕ ОКНО С БЛОКИРОВКОЙ ВВОДА ПРИ ПОЛЕТЕ И DRAG & DROP ──────────

class EdgeCompanionWindow(QFrame):
    """
    Парящее окно с поддержкой эффекта «приближения» (Hover Lift) при наведении,
    высококонтрастным Frosted Glass фоном, горячими клавишами, Drag & Drop перетаскиванием
    и блокировкой взаимодействия во время любых анимаций перемещения.
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
        self.is_flight_locked = False

        # Состояние Drag & Drop
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        self.drag_initial_y = 0
        self._lift_anim = None

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(12, 10, 12, 10)
        self.root_layout.setSpacing(8)

    def set_flight_locked(self, locked: bool):
        """Включает/выключает блокировку взаимодействия во время движения."""
        self.is_flight_locked = locked
        if locked:
            self.is_hovered = False
            self.is_dragging = False
            if self._lift_anim:
                self._lift_anim.stop()
            self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

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
        active = (self.is_hovered or self.is_dragging) and not self.is_flight_locked
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
        if self.is_flight_locked or not self.manager or not self.manager.is_companion_active or self.manager.is_flight_animating:
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
        if self.is_flight_locked or not self.manager or not self.manager.is_companion_active or self.manager.is_flight_animating:
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
        if self.is_flight_locked or self.is_dragging or (self.manager and self.manager.is_returning_to_window):
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
        if self.is_flight_locked or not self.manager or not self.manager.is_companion_active or self.manager.is_flight_animating:
            return

        # Панель настроек не перетаскивается
        if self.category == CardCategory.TOP_BAR:
            super().mousePressEvent(event)
            return

        pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        child = self.childAt(pos)

        # Проверяем интерактивность виджета или любого из его родителей (включая дроп-зоны и кнопки)
        is_interactive = False
        w = child
        while w and w is not self:
            if isinstance(w, (QLineEdit, QPushButton, QTableWidget, QHeaderView, ExcelDropZone)):
                is_interactive = True
                break
            w = w.parentWidget()

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

        if (self.is_flight_locked or self.manager.is_flight_animating) and not self.is_dragging:
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
        if self.is_flight_locked and not self.is_dragging:
            return

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
        """Обработка горячих клавиш (F11, Ctrl+D, Escape, Ctrl+R, F5, Ctrl+O) из любого парящего окна."""
        if not self.manager or not self.manager.is_companion_active:
            super().keyPressEvent(event)
            return

        # Возврат в главное окно (F11, Ctrl+D, Escape) — доступен всегда
        if event.key() == Qt.Key.Key_F11 or (
            event.key() == Qt.Key.Key_D and (event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        ) or event.key() == Qt.Key.Key_Escape:
            self.manager.exit_companion_mode()
            event.accept()
            return

        if self.is_flight_locked or self.manager.is_flight_animating:
            return

        # Запуск расчета (Ctrl+R, F5)
        if event.key() == Qt.Key.Key_F5 or (
            event.key() == Qt.Key.Key_R and (event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        ):
            self.manager.run_calculation()
            event.accept()
            return

        # Открыть шаблон (Ctrl+O)
        if event.key() == Qt.Key.Key_O and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            if hasattr(self.manager, 'win_files') and hasattr(self.manager.win_files, 'drop_tpl'):
                self.manager.win_files.drop_tpl.open_file_dialog()
                event.accept()
                return

        super().keyPressEvent(event)


# ─── 0. ВЕРХНЯЯ ПАНЕЛЬ НАСТРОЕК ─────────────────────────────────────────────────

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


# ─── 1. АУТЕНТИЧНАЯ КАРТОЧКА ФАЙЛОВ ─────────────────────────────────────────────

class AuthenticFilesWindow(EdgeCompanionWindow):
    """Карточка файлов: Шаблон, Аркус, Сохранение, Мастер замен с полным сохранением функций."""
    template_changed = Signal(str)
    arcus_changed = Signal(str)
    save_path_changed = Signal(str)
    replacement_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(CardCategory.FILES, parent)
        self.tpl_path = ""
        self.arc_path = ""
        self.save_path = ""
        self.excel_manager = ExcelManager()
        self.init_ui()

    def init_ui(self):
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(4)
        self.lbl_hdr = QLabel("⋮⋮  📁 Файлы и настройки", objectName="FieldLabel")
        self.lbl_hdr.setStyleSheet("font-size: 11px; font-weight: bold; color: #94A3B8;")
        hdr_row.addWidget(self.lbl_hdr)
        hdr_row.addStretch()
        self.root_layout.addLayout(hdr_row)

        self.drop_box = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        self.drop_box.setSpacing(8)

        self.drop_tpl = ExcelDropZone("Файл Шаблона", "Перетащите файл шаблона")
        self.drop_tpl.setMinimumHeight(48)
        self.drop_tpl.get_initial_dir = self._get_template_initial_dir
        self.drop_tpl.get_dialog_title = self._get_template_dialog_title
        self.drop_tpl.file_dropped.connect(self._on_tpl_dropped)

        self.drop_arc = ExcelDropZone("Файл Аркус", "Перетащите файл Аркус")
        self.drop_arc.setMinimumHeight(48)
        self.drop_arc.get_initial_dir = self._get_arcus_initial_dir
        self.drop_arc.get_dialog_title = self._get_arcus_dialog_title
        self.drop_arc.file_dropped.connect(self._on_arc_dropped)

        self.drop_box.addWidget(self.drop_tpl)
        self.drop_box.addWidget(self.drop_arc)
        self.root_layout.addLayout(self.drop_box)

        save_box = QHBoxLayout()
        save_box.setSpacing(6)
        self.lbl_save = QLabel("Сохранить:", objectName="FieldLabel")
        self.txt_save = QLineEdit()
        self.txt_save.setPlaceholderText("Путь к итоговому файлу...")
        self.txt_save.setMinimumHeight(28)
        self.txt_save.textChanged.connect(self._on_save_text_changed)
        self.txt_save.returnPressed.connect(self._on_save_return_pressed)

        self.btn_browse = QPushButton("Обзор...", objectName="SecondaryButton")
        self.btn_browse.setIcon(get_svg_icon("folder"))
        self.btn_browse.setMinimumHeight(28)
        self.btn_browse.clicked.connect(self._browse_save)

        save_box.addWidget(self.lbl_save)
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

    def _get_template_initial_dir(self) -> str:
        if self.manager:
            return self.manager.get_last_template_dir()
        return QSettings("WaterMetrics", "Directories").value("LastTemplateDir", "", type=str)

    def _get_arcus_initial_dir(self) -> str:
        if self.manager:
            return self.manager.get_last_arcus_dir()
        return QSettings("WaterMetrics", "Directories").value("LastArcusDir", "", type=str)

    def _get_template_dialog_title(self) -> str:
        if self.arc_path:
            return f"Выберите Файл Шаблона (Ранее выбран Аркус: {os.path.basename(self.arc_path)})"
        return "Выберите Файл Шаблона (.xlsx)"

    def _get_arcus_dialog_title(self) -> str:
        if self.tpl_path:
            return f"Выберите Файл Аркус (Ранее выбран Шаблон: {os.path.basename(self.tpl_path)})"
        return "Выберите Файл Аркус (Шаблон еще не выбран!)"

    def _on_tpl_dropped(self, path: str):
        if not path:
            return
        self.tpl_path = path

        # Сброс замен ИПУ для нового шаблона
        if self.manager and self.manager.main_win:
            main_win = self.manager.main_win
            had_closed = len(getattr(main_win, 'closed_meters', [])) > 0
            had_new = len(getattr(main_win, 'new_meters', [])) > 0
            if had_closed or had_new:
                main_win.closed_meters = []
                main_win.new_meters = []
                self.update_replacements_badge(0)
                self.manager.show_toast("Предыдущие замены ИПУ сброшены для нового шаблона", "INFO")

        out_dir = os.path.dirname(os.path.abspath(path))
        QSettings("WaterMetrics", "Directories").setValue("LastTemplateDir", out_dir)

        # Автоматический расчет имени следующего месяца
        try:
            out_filename = self.excel_manager.parse_house_and_next_month(path)
            last_out_dir = QSettings("WaterMetrics", "Directories").value("LastOutputDir", "", type=str) or out_dir
            full_save = os.path.join(last_out_dir, out_filename).replace('\\', '/')
            self.set_save_path(full_save)
            self.save_path_changed.emit(full_save)
        except Exception:
            pass

        self._update_file_linking_status()
        self.template_changed.emit(path)

    def _on_arc_dropped(self, path: str):
        if not path:
            return
        self.arc_path = path
        out_dir = os.path.dirname(os.path.abspath(path))
        QSettings("WaterMetrics", "Directories").setValue("LastArcusDir", out_dir)
        self._update_file_linking_status()
        self.arcus_changed.emit(path)

    def _on_save_text_changed(self, text: str):
        self.save_path = text
        self.save_path_changed.emit(text)

    def _on_save_return_pressed(self):
        if self.manager:
            self.manager.run_calculation()

    def _update_file_linking_status(self):
        accent = ThemeManager.get_current_accent_color()
        if self.tpl_path:
            tpl_name = os.path.basename(self.tpl_path)
            self.drop_tpl.set_highlight_state("linked", f"[ВЫБРАН] Шаблон: <b>{tpl_name}</b>")
        else:
            if self.arc_path:
                self.drop_tpl.set_highlight_state("warning", "[ВНИМАНИЕ] Требуется выбрать шаблон!")
            else:
                self.drop_tpl.set_highlight_state("default")

        if self.arc_path:
            arc_name = os.path.basename(self.arc_path)
            if self.tpl_path:
                tpl_name = os.path.basename(self.tpl_path)
                self.drop_arc.set_highlight_state("linked", f"[ВЫБРАН] Аркус: <b>{arc_name}</b><br/><span style='color:{accent};'>Связано с шаблоном: <b>{tpl_name}</b></span>")
            else:
                self.drop_arc.set_highlight_state("warning", f"[ВЫБРАН] Аркус: <b>{arc_name}</b><br/><span style='color:#F87171;'>Шаблон не выбран!</span>")
        else:
            self.drop_arc.set_highlight_state("default")

    def update_replacements_badge(self, count: int):
        accent = ThemeManager.get_current_accent_color()
        if count > 0:
            self.btn_repl.setText(f"Мастер замен ({count} замен)")
            self.btn_repl.setIcon(get_svg_icon("replace", color=accent))
            self.btn_repl.setToolTip(f"Зафиксировано замен ИПУ: {count} шт. Кликните для редактирования.")
        else:
            self.btn_repl.setText("Мастер замен счетчиков")
            self.btn_repl.setIcon(get_svg_icon("replace"))
            self.btn_repl.setToolTip("Открыть Мастер замен счетчиков ИПУ")

    def set_template_path(self, path: str):
        self.tpl_path = path
        self.drop_tpl.set_file_path(path)
        self._update_file_linking_status()

    def set_arcus_path(self, path: str):
        self.arc_path = path
        self.drop_arc.set_file_path(path)
        self._update_file_linking_status()

    def set_save_path(self, path: str):
        self.save_path = path
        self.txt_save.setText(path)

    def _browse_save(self):
        settings = QSettings("WaterMetrics", "Directories")
        last_out_dir = settings.value("LastOutputDir", "", type=str)
        init_path = self.save_path if self.save_path else (os.path.join(last_out_dir, "Отчет.xlsx") if last_out_dir else "Отчет.xlsx")

        f, _ = QFileDialog.getSaveFileName(self, "Сохранить отчет", init_path, "Excel (*.xlsx)")
        if f:
            out_dir = os.path.dirname(os.path.abspath(f))
            settings.setValue("LastOutputDir", out_dir)
            self.set_save_path(f)
            self.save_path_changed.emit(f)


# ─── 2. АУТЕНТИЧНАЯ КАРТОЧКА ПОКАЗАТЕЛЕЙ ───────────────────────────────────

class AuthenticValuesWindow(EdgeCompanionWindow):
    """Карточка показателей: ХВС, ГВС, ДОБ., Сумма с поддержкой множественной вставки из Excel."""
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

        self.txt_cold.returnPressed.connect(self.txt_hot.setFocus)
        self.txt_hot.returnPressed.connect(self.txt_corr.setFocus)
        self.txt_corr.returnPressed.connect(self._on_corr_return_pressed)

        self.root_layout.addLayout(grid)

        self.lbl_sum = QLabel("Сумма: 0.00 м³", objectName="FieldLabel")
        accent = ThemeManager.get_current_accent_color()
        self.lbl_sum.setStyleSheet(f"font-weight: 700; font-size: 12px; color: {accent};")
        self.root_layout.addWidget(self.lbl_sum)

        self.txt_cold.textChanged.connect(self._on_changed)
        self.txt_hot.textChanged.connect(self._on_changed)
        self.txt_corr.textChanged.connect(self._on_changed)

    def _on_corr_return_pressed(self):
        if self.manager and hasattr(self.manager, 'win_files'):
            self.manager.win_files.txt_save.setFocus()
            self.manager.win_files.txt_save.selectAll()

    def _create_input(self, label: str, layout: QHBoxLayout) -> SmartNumericLineEdit:
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
    """Карточка истории отчетов с идеальной геометрией (без выпираний и обрезаний), контекстным меню и двойным кликом."""
    history_changed = Signal()

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
        self.table_hist.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table_hist.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table_hist.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_hist.setColumnWidth(0, 130)
        self.table_hist.verticalHeader().setVisible(False)
        self.table_hist.setMinimumHeight(85)
        self.table_hist.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table_hist.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_hist.customContextMenuRequested.connect(self._show_context_menu)
        self.table_hist.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.table_hist.itemDoubleClicked.connect(self._on_item_double_clicked)

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
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(4)

        btn_style = """
            QPushButton {
                font-size: 10px;
                font-weight: 600;
                padding: 4px 4px;
                border-radius: 6px;
            }
        """

        self.btn_open = QPushButton("Открыть", objectName="SecondaryButton")
        self.btn_open.setIcon(get_svg_icon("folder"))
        self.btn_open.setStyleSheet(btn_style)
        self.btn_open.setMinimumHeight(26)
        self.btn_open.clicked.connect(self._open_selected)

        self.btn_folder = QPushButton("В папку", objectName="SecondaryButton")
        self.btn_folder.setIcon(get_svg_icon("folder"))
        self.btn_folder.setStyleSheet(btn_style)
        self.btn_folder.setMinimumHeight(26)
        self.btn_folder.clicked.connect(self._show_in_folder)

        self.btn_clr = QPushButton("Удалить", objectName="SecondaryButton")
        self.btn_clr.setIcon(get_svg_icon("trash"))
        self.btn_clr.setStyleSheet(btn_style)
        self.btn_clr.setMinimumHeight(26)
        self.btn_clr.clicked.connect(self._remove_selected)

        self.btn_clear_all = QPushButton("Очистить", objectName="SecondaryButton")
        self.btn_clear_all.setIcon(get_svg_icon("trash", color="#F87171"))
        self.btn_clear_all.setStyleSheet(btn_style)
        self.btn_clear_all.setMinimumHeight(26)
        self.btn_clear_all.clicked.connect(self._clear_all)

        btn_row.addWidget(self.btn_open, 1)
        btn_row.addWidget(self.btn_folder, 1)
        btn_row.addWidget(self.btn_clr, 1)
        btn_row.addWidget(self.btn_clear_all, 1)
        self.root_layout.addLayout(btn_row)

    def _show_context_menu(self, pos: QPoint):
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
                if sys.platform == 'win32':
                    try:
                        os.startfile(full_path)
                    except Exception:
                        QDesktopServices.openUrl(QUrl.fromLocalFile(full_path))
                else:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(full_path))
        elif chosen == action_copy:
            if full_path:
                QApplication.clipboard().setText(full_path)
                if self.manager:
                    self.manager.show_toast("Путь скопирован в буфер обмена!", "SUCCESS")
        elif chosen == action_delete:
            self.table_hist.removeRow(row)
            self._save_current_history()

    def _on_cell_double_clicked(self, row: int, column: int):
        path_item = self.table_hist.item(row, 1)
        if path_item:
            fp = os.path.normpath(path_item.text())
            if os.path.exists(fp):
                if sys.platform == 'win32':
                    try:
                        os.startfile(fp)
                    except Exception:
                        QDesktopServices.openUrl(QUrl.fromLocalFile(fp))
                else:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(fp))
            else:
                if self.manager:
                    self.manager.show_toast(f"Файл не найден: {os.path.basename(fp)}", "ERROR")

    def _on_item_double_clicked(self, item: QTableWidgetItem):
        self._on_cell_double_clicked(item.row(), item.column())

    def _open_selected(self):
        selected_rows = sorted(list(set(index.row() for index in self.table_hist.selectedIndexes())))
        if not selected_rows:
            if self.manager:
                self.manager.show_toast("Выберите файлы из таблицы истории!", "INFO")
            return

        opened_count = 0
        for row in selected_rows:
            path_item = self.table_hist.item(row, 1)
            if path_item:
                fp = os.path.normpath(path_item.text())
                if os.path.exists(fp):
                    if sys.platform == 'win32':
                        try:
                            os.startfile(fp)
                            opened_count += 1
                        except Exception:
                            if QDesktopServices.openUrl(QUrl.fromLocalFile(fp)):
                                opened_count += 1
                    else:
                        if QDesktopServices.openUrl(QUrl.fromLocalFile(fp)):
                            opened_count += 1
                else:
                    if self.manager:
                        self.manager.show_toast(f"Файл не найден: {os.path.basename(fp)}", "ERROR")
        if opened_count > 0 and self.manager:
            self.manager.show_toast(f"Открыто файлов: {opened_count}", "SUCCESS")

    def _show_in_folder(self):
        selected_rows = sorted(list(set(index.row() for index in self.table_hist.selectedIndexes())))
        if not selected_rows:
            if self.manager:
                self.manager.show_toast("Выберите файл из таблицы истории!", "INFO")
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
                        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(fp)))
                else:
                    if self.manager:
                        self.manager.show_toast("Файл не найден на диске!", "ERROR")

    def _remove_selected(self):
        selected_rows = sorted(list(set(index.row() for index in self.table_hist.selectedIndexes())), reverse=True)
        if not selected_rows:
            if self.manager:
                self.manager.show_toast("Выберите строки для удаления из списка!", "INFO")
            return

        count = len(selected_rows)
        for row in selected_rows:
            self.table_hist.removeRow(row)

        self._save_current_history()
        if self.manager:
            self.manager.show_toast(f"Удалено строк из списка: {count}", "SUCCESS")

    def _clear_all(self):
        if self.table_hist.rowCount() == 0:
            if self.manager:
                self.manager.show_toast("История отчетов уже пуста!", "INFO")
            return

        self.table_hist.setRowCount(0)
        HistoryService.clear()
        self._sync_to_dashboard()
        if self.manager:
            self.manager.show_toast("История отчетов очищена!", "SUCCESS")

    def _save_current_history(self):
        remaining_paths = []
        for r in range(self.table_hist.rowCount()):
            item = self.table_hist.item(r, 1)
            if item:
                remaining_paths.append(item.text())
        HistoryService.save(remaining_paths)
        self._sync_to_dashboard()

    def _sync_to_dashboard(self):
        if self.manager and self.manager.main_win:
            p_main = getattr(self.manager.main_win, 'page_main', None)
            if p_main and hasattr(p_main, 'table_hist'):
                p_main.table_hist.setRowCount(0)
                for r in range(self.table_hist.rowCount()):
                    p_main.table_hist.insertRow(r)
                    item0 = self.table_hist.item(r, 0)
                    item1 = self.table_hist.item(r, 1)
                    if item0:
                        p_main.table_hist.setItem(r, 0, QTableWidgetItem(item0.text()))
                    if item1:
                        p_main.table_hist.setItem(r, 1, QTableWidgetItem(item1.text()))
                if hasattr(p_main, '_update_kpi_metrics'):
                    p_main._update_kpi_metrics()

    def add_history_entry(self, full_path: str, save_to_service: bool = True):
        if not full_path:
            return
        filename = os.path.basename(full_path)
        for r in range(self.table_hist.rowCount()):
            item = self.table_hist.item(r, 1)
            if item and os.path.normpath(item.text()) == os.path.normpath(full_path):
                return

        row = self.table_hist.rowCount()
        self.table_hist.insertRow(row)
        self.table_hist.setItem(row, 0, QTableWidgetItem(filename))
        self.table_hist.setItem(row, 1, QTableWidgetItem(full_path))

        if save_to_service:
            HistoryService.add_path(full_path)
        self._sync_to_dashboard()

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

    def set_running_state(self, is_running: bool):
        if is_running:
            self.btn_run.setEnabled(False)
            self.btn_run.setText("⏳ Выполняется расчет...")
        else:
            self.btn_run.setEnabled(True)
            self.btn_run.setText("⚡ Сформировать файл отчета")


# ─── 5. ГЛАВНЫЙ МЕНЕДЖЕР РЕЖИМА НАБИВКИ (COMPANION DOCK MANAGER) ───────────────

class CompanionModeManager:
    """
    Бесшовный координатор режима набивки:
    1. Полная блокировка взаимодействия во время анимаций полета/парковки.
    2. 100% интерактивность сразу после завершения полета (в т.ч. на 1 сек паузы).
    3. Полное сохранение всех функций (замены ИПУ, выбор папок, умный ввод, история).
    4. Точный старт из 4 элементов дашборда с динамическим морфингом размеров.
    5. Поддержка Drag & Drop изменения порядка карточек строго в пределах док-колонки.
    6. Надежный возврат в главное окно.
    """

    def __init__(self, main_win):
        self.main_win = main_win
        self.is_companion_active = False
        self.is_returning_to_window = False
        self.is_flight_animating = False
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
            self.win_files: 235,
            self.win_values: 115,
            self.win_hist: 200,
            self.win_run: 56,
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
        self.leave_timer.setInterval(400)
        self.leave_timer.timeout.connect(self._collapse_dock_together)

        # 2-секундный сторожевой таймер (Watchdog) для разрешения спорных ситуаций и самовосстановления
        self.watchdog_timer = QTimer()
        self.watchdog_timer.setInterval(2000)
        self.watchdog_timer.timeout.connect(self._watchdog_check)

        self._load_settings()
        self._connect_signals()
        ThemeManager.on_theme_changed.append(self.update_theme_styles)

    def set_all_cards_flight_locked(self, locked: bool):
        """Блокирует или разблокирует ввод на всех карточках."""
        self.is_flight_animating = locked
        if locked:
            self.proximity_timer.stop()
            self.leave_timer.stop()
        else:
            if self.is_companion_active and not self.is_returning_to_window:
                self.proximity_timer.start()
        for card in self.cards:
            card.set_flight_locked(locked)

    def raise_all_cards(self):
        """Поднимает все карточки режима набивки поверх других приложений (Excel/1C)."""
        for card in self.cards:
            card.raise_()

    def show_toast(self, message: str, level: str = "INFO"):
        """Выводит Toast-уведомление поверх карточек режима набивки."""
        target_win = self.win_top_bar if self.win_top_bar.isVisible() else (self.cards[0] if self.cards else self.main_win)
        if isinstance(target_win, QWidget):
            ToastNotification.show_toast(target_win, message, level)

    def get_last_template_dir(self) -> str:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        settings = QSettings("WaterMetrics", "Directories")
        return settings.value("LastTemplateDir", base_dir, type=str)

    def get_last_arcus_dir(self) -> str:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        settings = QSettings("WaterMetrics", "Directories")
        return settings.value("LastArcusDir", base_dir, type=str)

    def get_last_output_dir(self) -> str:
        settings = QSettings("WaterMetrics", "Directories")
        return settings.value("LastOutputDir", "", type=str)

    def update_replacements_badge(self):
        """Обновляет индикатор замен счетчиков в доке и дашборде."""
        count = len(getattr(self.main_win, 'closed_meters', []))
        self.win_files.update_replacements_badge(count)
        p_main = getattr(self.main_win, 'page_main', None)
        if p_main and hasattr(p_main, 'btn_repl'):
            accent = ThemeManager.get_current_accent_color()
            if count > 0:
                p_main.btn_repl.setText(f"Мастер замен ({count} замен)")
                p_main.btn_repl.setIcon(get_svg_icon("replace", color=accent))
            else:
                p_main.btn_repl.setText("Мастер замен счетчиков")
                p_main.btn_repl.setIcon(get_svg_icon("replace"))

    def open_replacement_dialog(self):
        """Открывает Мастер замен счетчиков поверх режима набивки."""
        tpl_path = self.win_files.tpl_path
        if not tpl_path:
            p_main = getattr(self.main_win, 'page_main', None)
            if p_main and hasattr(p_main, 'drop_tpl'):
                tpl_path = p_main.drop_tpl.file_path

        if not tpl_path or not os.path.exists(tpl_path):
            self.show_toast("Сначала выберите файл шаблона!", "ERROR")
            return

        excel_manager = getattr(self.main_win, 'excel_manager', ExcelManager())
        apts_data = excel_manager.extract_apartments_and_meters(tpl_path)

        dlg = MeterReplacementDialog(
            self.win_files,
            apts_data,
            getattr(self.main_win, 'closed_meters', []),
            getattr(self.main_win, 'new_meters', [])
        )
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            closed, new = dlg.get_results()
            if hasattr(self.main_win, 'closed_meters'):
                self.main_win.closed_meters = closed
            if hasattr(self.main_win, 'new_meters'):
                self.main_win.new_meters = new

            self.update_replacements_badge()
            self.show_toast(f"Зафиксировано замен: {len(closed)}", "SUCCESS")
            p_main = getattr(self.main_win, 'page_main', None)
            if p_main and hasattr(p_main, '_update_kpi_metrics'):
                p_main._update_kpi_metrics()

    def _connect_signals(self):
        self.win_top_bar.restore_requested.connect(self.exit_companion_mode)
        self.win_top_bar.switch_side_requested.connect(self.toggle_dock_side)

        self.win_files.template_changed.connect(self._sync_tpl_to_main)
        self.win_files.arcus_changed.connect(self._sync_arc_to_main)
        self.win_files.save_path_changed.connect(self._sync_save_to_main)
        self.win_files.replacement_clicked.connect(self.open_replacement_dialog)

        self.win_values.values_changed.connect(self._sync_values_to_main)
        self.win_run.run_requested.connect(self.run_calculation)

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
            if hasattr(win, '_update_file_linking_status'):
                win._update_file_linking_status()

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

        # Блокируем взаимодействие на время перелета
        self.set_all_cards_flight_locked(True)

        group = QParallelAnimationGroup()
        for card in self.cards:
            target_y = target_positions[card]
            h = self._get_card_height(card)
            card.base_docked_x = open_x
            card.is_dock_expanded = self.is_dock_expanded

            anim = QPropertyAnimation(card, b"geometry")
            anim.setDuration(350)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.setStartValue(card.geometry())
            anim.setEndValue(QRect(target_x, target_y, self.dock_width, h))
            group.addAnimation(anim)

        def on_toggle_done():
            self.set_all_cards_flight_locked(False)
            for c in self.cards:
                c.base_docked_x = open_x
                c.is_dock_expanded = self.is_dock_expanded
            self.raise_all_cards()
            self._check_dock_proximity()

        group.finished.connect(on_toggle_done)
        self._active_anim_group = group
        group.start()
        self.show_toast(f"Панели перемещены {side_text.lower()}", "INFO")

    def enter_companion_mode(self):
        """Бесшовный старт: окна появляются ровно в координатах дашборда и плавно летят к краю."""
        if self.is_companion_active:
            return

        if self._active_anim_group:
            self._active_anim_group.stop()

        self.is_companion_active = True
        self.is_returning_to_window = False
        self.watchdog_timer.start()
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

        self.update_replacements_badge()
        self.saved_card_geometries = self._read_dashboard_geometries()

        screen = QApplication.screenAt(self.main_win.pos()) or QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        target_positions = self._calculate_dock_positions(screen_geo)
        open_x = self._get_open_x(screen_geo)

        # 1. Синхронизируем сторону и кнопку
        self.win_top_bar.btn_side.setText("⇄ Справа" if self.dock_side == DockSide.LEFT else "⇄ Слева")
        for card in self.cards:
            card.dock_side = self.dock_side

        # 2. Начальное положение верхней панели: появляется сверху в док-колонке
        start_top_y = screen_geo.top() - 60
        self.win_top_bar.setGeometry(QRect(open_x, start_top_y, self.dock_width, self._get_card_height(self.win_top_bar)))
        self.win_top_bar.show()

        # 3. Контентные карточки появляются РОВНО на месте и в РАЗМЕРАХ карточек дашборда
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

        # БЛОКИРУЕМ ВЗАИМОДЕЙСТВИЕ НА ВРЕМЯ ПОЛЕТА
        self.set_all_cards_flight_locked(True)

        # 5. Плавная морфинг-анимация полета ВСЕХ 5 окон к док-колонке
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
            # РАЗБЛОКИРУЕМ ВЗАИМОДЕЙСТВИЕ: карточки встали на место и доступны на 1 секунду!
            self.set_all_cards_flight_locked(False)
            self.watchdog_timer.start()
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

        # БЛОКИРУЕМ ВЗАИМОДЕЙСТВИЕ НА ВРЕМЯ ПАРКОВКИ
        self.set_all_cards_flight_locked(True)

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
            for c in self.cards:
                c.is_dock_expanded = False
            self.set_all_cards_flight_locked(False)
            self.raise_all_cards()

        group.finished.connect(on_park_done)
        self._active_anim_group = group
        group.start()

    def _watchdog_check(self):
        """
        Сторожевой таймер (срабатывает раз в 2 секунды):
        1. Проверяет глобальное положение мыши.
        2. Разрешает любые спорные / зависшие состояния (сброс застрявших флагов анимации).
        3. Корректно выдвигает или задвигает док в зависимости от позиции курсора.
        """
        if not self.is_companion_active or self.is_returning_to_window:
            return

        # Если идет реальный Drag&Drop карточки пользователем, не вмешиваемся
        if any(c.is_dragging for c in self.cards):
            return

        # Если флаги анимации зависли, принудительно разблокируем
        if self.is_flight_animating or self._animating_dock:
            if not self._active_anim_group or self._active_anim_group.state() != QParallelAnimationGroup.State.Running:
                self.is_flight_animating = False
                self._animating_dock = False
                self.set_all_cards_flight_locked(False)

        # Синхронизируем положение по мыши
        self._check_dock_proximity()

    def _check_dock_proximity(self):
        """Проверка приближения/ухода мыши: плавный и стабильный выезд/заезд дока."""
        if not self.is_companion_active or self.is_returning_to_window or self._animating_dock or self.is_flight_animating:
            return
        if any(c.is_dragging for c in self.cards):
            return

        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos) or QApplication.screenAt(self.cards[0].pos()) or QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()

        # Вертикальная зона охвата: щедрый диапазон по всей высоте экрана
        target_positions = self._calculate_dock_positions(screen_geo)
        min_y = min(target_positions.values()) - 60
        max_y = max(target_positions[c] + self._get_card_height(c) for c in self.cards) + 60
        is_in_y = min_y <= cursor_pos.y() <= max_y

        if self.dock_side == DockSide.RIGHT:
            if self.is_dock_expanded:
                # В раскрытом состоянии зона удержания шире на 80px влево от дока
                is_in_dock_zone = (cursor_pos.x() >= (screen_geo.right() - self.dock_width - 80)) and is_in_y
            else:
                # В закрытом состоянии выезд срабатывает при приближении к правому краю (< 85px)
                is_in_dock_zone = (cursor_pos.x() >= (screen_geo.right() - 85)) and is_in_y
        else:
            # ЛЕВАЯ СТОРОНА
            if self.is_dock_expanded:
                is_in_dock_zone = (cursor_pos.x() <= (screen_geo.left() + self.dock_width + 80)) and is_in_y
            else:
                is_in_dock_zone = (cursor_pos.x() <= (screen_geo.left() + 85)) and is_in_y

        # Проверка прямого нахождения курсора над любой из карточек (с охранным периметром 10px)
        is_over_card = any(
            c.geometry().adjusted(-10, -10, 10, 10).contains(cursor_pos)
            for c in self.cards
        )

        should_be_expanded = is_in_dock_zone or is_over_card

        if should_be_expanded:
            self.leave_timer.stop()
            if not self.is_dock_expanded and not self._animating_dock:
                self._expand_dock_together()
        else:
            if self.is_dock_expanded and not self._animating_dock:
                if not self.leave_timer.isActive():
                    self.leave_timer.start()

    def _expand_dock_together(self):
        """Единый синхронный выезд ВСЕГО дока при приближении мыши."""
        if not self.is_companion_active or self.is_returning_to_window:
            return

        if self._active_anim_group:
            self._active_anim_group.stop()

        self._animating_dock = True
        self.set_all_cards_flight_locked(True)

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
            anim.setDuration(220)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.setStartValue(card.geometry())
            anim.setEndValue(QRect(open_x, target_y, self.dock_width, h))
            group.addAnimation(anim)

        def on_expand_done():
            self._animating_dock = False
            self.is_dock_expanded = True
            for c in self.cards:
                c.is_dock_expanded = True
                c.base_docked_x = open_x
            self.set_all_cards_flight_locked(False)
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
        self.set_all_cards_flight_locked(True)

        screen = QApplication.screenAt(self.cards[0].pos()) or QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()
        target_positions = self._calculate_dock_positions(screen_geo)
        park_x = self._get_park_x(screen_geo)

        group = QParallelAnimationGroup()
        for card in self.cards:
            target_y = target_positions[card]
            h = self._get_card_height(card)

            anim = QPropertyAnimation(card, b"geometry")
            anim.setDuration(220)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.setStartValue(card.geometry())
            anim.setEndValue(QRect(park_x, target_y, self.dock_width, h))
            group.addAnimation(anim)

        def on_collapse_done():
            self._animating_dock = False
            self.is_dock_expanded = False
            for c in self.cards:
                c.is_dock_expanded = False
            self.set_all_cards_flight_locked(False)
            self.raise_all_cards()

        group.finished.connect(on_collapse_done)
        self._active_anim_group = group
        group.start()

    # ─── DRAG & DROP REORDERING ───────────────────────────────────────────

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
        if hasattr(self, 'watchdog_timer'):
            self.watchdog_timer.stop()

        if self._active_anim_group:
            self._active_anim_group.stop()

        # Блокируем взаимодействие
        self.set_all_cards_flight_locked(True)

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
            self._sync_save_to_main(self.win_files.save_path)
            self._sync_values_to_main(
                self.win_values.txt_cold.text(),
                self.win_values.txt_hot.text(),
                self.win_values.txt_corr.text()
            )

        def restore_main_window():
            for card in self.cards:
                card.hide()
                card.set_flight_locked(False)

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
            self.is_flight_animating = False
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

    def run_calculation(self):
        """Запуск расчета водопотребления из режима набивки."""
        if not self.is_companion_active or self.is_returning_to_window or self.is_flight_animating:
            return

        tpl = self.win_files.tpl_path
        arc = self.win_files.arc_path
        sav = self.win_files.save_path

        if not tpl or not arc or not sav:
            self.show_toast("Укажите все пути к Excel файлам!", "ERROR")
            return

        try:
            float(self.win_values.txt_cold.text().replace(',', '.'))
            float(self.win_values.txt_hot.text().replace(',', '.'))
            float(self.win_values.txt_corr.text().replace(',', '.'))
        except ValueError:
            self.show_toast("Ошибка в числовых параметрах ввода!", "ERROR")
            return

        out_dir = os.path.dirname(os.path.abspath(sav))
        QSettings("WaterMetrics", "Directories").setValue("LastOutputDir", out_dir)

        self._sync_tpl_to_main(tpl)
        self._sync_arc_to_main(arc)
        self._sync_save_to_main(sav)
        self._sync_values_to_main(
            self.win_values.txt_cold.text(),
            self.win_values.txt_hot.text(),
            self.win_values.txt_corr.text()
        )

        self.win_run.set_running_state(True)
        if hasattr(self.main_win, 'run_calculation'):
            self.main_win.run_calculation()

    def on_calculation_finished(self, success: bool, message: str):
        """Обработка завершения расчета и вывод статуса прямо в режиме набивки."""
        self.win_run.set_running_state(False)
        if self.is_companion_active:
            if success:
                self.show_toast("Файл успешно сформирован!", "SUCCESS")
            else:
                self.show_toast(f"Ошибка расчета: {message}", "ERROR")
