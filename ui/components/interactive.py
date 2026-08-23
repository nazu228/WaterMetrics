# ui/components/interactive.py
"""
Модуль интерактивных компонентов UI для WaterMetrics.
Стиль: Apple Frosted Glass / Glassmorphism.
"""

import os
import math
import random
from datetime import datetime
from typing import List, Dict

from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, QRectF, QEvent, Signal, QPoint, QEasingCurve, QPropertyAnimation, QSize
from PySide6.QtGui import QFont, QColor, QPainter, QPainterPath, QPen, QBrush, QDragEnterEvent, QDropEvent, QLinearGradient

from ui.styles import ThemeManager
from ui.components.glass_icon import GlassIconWidget


class HoverGlassCard(QFrame):
    """Стеклянная карточка с эффектом Frosted Glass и подсвечиваемой гранью при наведении."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def enterEvent(self, event: QEvent):
        self.setProperty("hover", True)
        self.style().unpolish(self)
        self.style().polish(self)
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        self.setProperty("hover", False)
        self.style().unpolish(self)
        self.style().polish(self)
        super().leaveEvent(event)


class ExcelDropZone(QFrame):
    """
    Интерактивная Drag-and-Drop зона для файлов Excel.
    Клик по ЛЮБОЙ области карточки (или перетаскивание) открывает диалог выбора файла.
    """
    file_dropped = Signal(str)

    def __init__(self, title: str, placeholder: str = "Перетащите .xlsx файл или кликните сюда", parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.file_path = ""
        self.title = title
        self.placeholder = placeholder
        self.is_compact = False
        self.init_ui()

    def init_ui(self):
        self.setObjectName("GlassCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumSize(180, 96)

        self.box_layout = QVBoxLayout(self)
        self.box_layout.setContentsMargins(10, 8, 10, 8)
        self.box_layout.setSpacing(3)
        self.box_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_badge = GlassIconWidget("folder", size=QSize(28, 28))
        self.icon_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_title = QLabel(self.title, objectName="DropZoneTitle")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setWordWrap(False)

        self.lbl_status = QLabel(self.placeholder, objectName="DropZoneStatus")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setWordWrap(False)

        self.box_layout.addWidget(self.icon_badge, 0, Qt.AlignmentFlag.AlignCenter)
        self.box_layout.addWidget(self.lbl_title)
        self.box_layout.addWidget(self.lbl_status)

        ThemeManager.on_theme_changed.append(self._update_theme_colors)
        self._update_theme_colors()

    def _update_theme_colors(self, theme_name: str = None, **kwargs):
        accent = ThemeManager.get_current_accent_color()
        curr_theme = theme_name or ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        
        title_color = accent if not is_light else ("#0A246A" if curr_theme == "Как дома" else "#028090")
        sub_color = "#444444" if is_light else "#94A3B8"
        
        if hasattr(self, 'icon_badge'):
            self.icon_badge.set_color(title_color)

        self.lbl_title.setStyleSheet(f"color: {title_color}; font-size: 12px; font-weight: bold; background: transparent;")
        if not self.file_path:
            self.lbl_status.setStyleSheet(f"color: {sub_color}; font-size: 10px; background: transparent;")

    def set_compact_mode(self, is_compact: bool):
        """Адаптивный компактный режим для малых размеров карточек."""
        self.is_compact = is_compact
        if is_compact:
            self.icon_badge.setVisible(False)
            if not self.file_path:
                self.lbl_status.setVisible(False)
            else:
                self.lbl_status.setVisible(True)
            self.setMinimumHeight(45)
            self.box_layout.setContentsMargins(4, 2, 4, 2)
        else:
            self.icon_badge.setVisible(True)
            self.lbl_status.setVisible(True)
            self.setMinimumHeight(96)
            self.box_layout.setContentsMargins(10, 8, 10, 8)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        h = self.height()
        w = self.width()
        
        if h < 65:
            self.icon_badge.setVisible(False)
            self.box_layout.setContentsMargins(4, 2, 4, 2)
            self.box_layout.setSpacing(1)
        elif h < 95:
            self.icon_badge.setVisible(w > 160)
            self.icon_badge.setFixedSize(26, 26)
            self.box_layout.setContentsMargins(6, 4, 6, 4)
            self.box_layout.setSpacing(2)
        else:
            self.icon_badge.setVisible(True)
            self.icon_badge.setFixedSize(28, 28)
            self.box_layout.setContentsMargins(10, 8, 10, 8)
            self.box_layout.setSpacing(3)
            
        self._update_elided_status_text()

    def _get_title_color(self) -> str:
        curr_theme = ThemeManager.get_current_theme_name()
        accent = ThemeManager.get_current_accent_color()
        if curr_theme == "Как дома":
            return "#0A246A"
        elif curr_theme == "Pearl Light":
            return "#028090"
        return accent

    def _update_elided_status_text(self):
        if not self.file_path or not os.path.exists(self.file_path):
            return
        filename = os.path.basename(self.file_path)
        fm = self.lbl_status.fontMetrics()
        max_w = max(60, self.width() - 20)
        elided_filename = fm.elidedText(filename, Qt.TextElideMode.ElideMiddle, max_w)
        
        try:
            sz_bytes = os.path.getsize(self.file_path)
            sz_str = f"{sz_bytes / 1024:.1f} KB" if sz_bytes < 1024 * 1024 else f"{sz_bytes / (1024 * 1024):.2f} MB"
            meta_info = f"<br/><span style='color: #888888; font-size: 9px;'>📄 {sz_str}</span>"
        except Exception:
            meta_info = ""

        if self.height() < 65:
            self.lbl_status.setText(f"✓ <b>{elided_filename}</b>")
        else:
            self.lbl_status.setText(f"✓ <b>{elided_filename}</b>{meta_info}")

    def set_file_path(self, path: str):
        self.file_path = path
        if path and os.path.exists(path):
            self._update_elided_status_text()
            self.lbl_status.setStyleSheet("color: #10B981; font-size: 11px; font-weight: bold; background: transparent;")
        else:
            self.lbl_status.setText(self.placeholder)
            self._update_theme_colors()

        if self.is_compact and self.file_path:
            self.lbl_status.setVisible(True)
        self.file_dropped.emit(path)

    def mousePressEvent(self, event):
        """Клик по любой области карточки вызывает окно выбора файла."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_file_dialog()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            if any(url.toLocalFile().endswith(('.xlsx', '.xls')) for url in event.mimeData().urls()):
                event.acceptProposedAction()
                self.setProperty("drag", True)
                self.style().unpolish(self)
                self.style().polish(self)

    def dragLeaveEvent(self, event):
        self.setProperty("drag", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event):
        self.dragLeaveEvent(event)
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.endswith(('.xlsx', '.xls')):
                self.set_file_path(path)
                break

    def open_file_dialog(self):
        """Публичный вызов диалога выбора файла."""
        self._open_file_dialog()

    def _open_file_dialog(self):
        start_dir = ""
        if callable(getattr(self, 'get_initial_dir', None)):
            start_dir = self.get_initial_dir()
        elif hasattr(self, 'initial_dir') and self.initial_dir:
            start_dir = self.initial_dir

        dialog_title = f"Выберите {self.title}"
        if callable(getattr(self, 'get_dialog_title', None)):
            custom_title = self.get_dialog_title()
            if custom_title:
                dialog_title = custom_title

        path, _ = QFileDialog.getOpenFileName(self, dialog_title, start_dir, "Excel (*.xlsx *.xls)")
        if path:
            self.set_file_path(path)

    def clear_file(self):
        """Очистить ранее выбранный файл."""
        self.file_path = ""
        self.lbl_status.setText(self.placeholder)
        self._update_theme_colors()
        self.file_dropped.emit("")

    def set_highlight_state(self, state: str, message: str = ""):
        """Визуальное подсвечивание связки файлов."""
        self.setProperty("state", state)
        self.style().unpolish(self)
        self.style().polish(self)
        accent = ThemeManager.get_current_accent_color()
        if message:
            self.lbl_status.setText(message)
            if state == "linked":
                self.lbl_status.setStyleSheet(f"color: {accent}; font-size: 11px; font-weight: bold; background: transparent;")
            elif state == "warning":
                self.lbl_status.setStyleSheet("color: #F87171; font-size: 11px; font-weight: bold; background: transparent;")
        elif not self.file_path:
            self.lbl_status.setText(self.placeholder)
            self.lbl_status.setStyleSheet("color: #94A3B8; font-size: 11px; background: transparent;")


class WaterGaugeWidget(QWidget):
    """Оптимизированный гидравлический индикатор с Event-driven анимацией и 0% CPU в idle."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(80, 100)

        self.fill_level = 0.0
        self.target_level = 0.0
        self.phase1 = 0.0
        self.phase2 = 1.5

        self.bubbles = []
        self._init_bubbles()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_frame)
        # В режиме простоя (0% уровень) таймер отключен для экономии CPU

    def _init_bubbles(self):
        for _ in range(10):
            self.bubbles.append({
                'x': random.uniform(15, 65),
                'y': random.uniform(20, 90),
                'r': random.uniform(1.2, 2.5),
                'speed': random.uniform(0.6, 1.5),
                'wobble': random.uniform(0, 6.28)
            })

    def set_level(self, pct: float):
        self.target_level = max(0.0, min(1.0, pct))
        if (abs(self.fill_level - self.target_level) > 0.001 or self.target_level > 0.0) and not self.timer.isActive():
            if self.isVisible():
                self.timer.start(33)
        self.update()

    def hideEvent(self, event):
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        super().hideEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, 'timer') and not self.timer.isActive():
            if self.fill_level > 0.001 or abs(self.fill_level - self.target_level) > 0.001:
                self.timer.start(33)

    def _animate_frame(self):
        if not self.isVisible():
            if self.timer.isActive():
                self.timer.stop()
            return

        self.phase1 += 0.08
        self.phase2 += 0.05

        level_diff = self.target_level - self.fill_level
        if abs(level_diff) > 0.001:
            self.fill_level += level_diff * 0.06
        else:
            self.fill_level = self.target_level
            if self.fill_level <= 0.001:
                self.fill_level = 0.0
                if self.timer.isActive():
                    self.timer.stop()
                self.update()
                return

        w_height = (self.height() - 16) * self.fill_level
        water_surface_y = (self.height() - 8) - w_height

        for b in self.bubbles:
            b['y'] -= b['speed']
            b['wobble'] += 0.05
            b['x'] += math.sin(b['wobble']) * 0.3

            if b['y'] < water_surface_y or b['y'] < 10:
                b['y'] = self.height() - 10
                b['x'] = random.uniform(10, max(15, self.width() - 10))

        self.update()

    def paintEvent(self, event):
        painter = QPainter()
        if not painter.begin(self):
            return

        try:
            accent_hex = ThemeManager.get_current_accent_color()
            base_col = QColor(accent_hex)

            painter.setRenderHint(QPainter.Antialiasing)
            w, h = self.width(), self.height()
            rect = QRectF(4, 4, max(1.0, w - 8), max(1.0, h - 8))

            # 1. Задний фон колбы
            painter.setPen(QPen(QColor(base_col.red(), base_col.green(), base_col.blue(), 80), 1.5))
            painter.setBrush(QBrush(QColor(15, 23, 42, 220)))
            painter.drawRoundedRect(rect, 12, 12)

            if self.fill_level <= 0.01:
                self._draw_glass_overlay(painter, rect, w, h, base_col)
                return

            # 2. Клиппинг воды строго внутри границы карточки
            clip_path = QPainterPath()
            clip_path.addRoundedRect(rect, 12, 12)
            painter.setClipPath(clip_path)

            water_height = rect.height() * self.fill_level
            surface_y = rect.bottom() - water_height

            # 3. Задняя волна
            back_wave = QPainterPath()
            back_wave.moveTo(rect.left() - 5, rect.bottom() + 5)
            back_wave.lineTo(rect.left() - 5, surface_y)

            x = rect.left() - 5
            while x <= rect.right() + 5:
                y = surface_y + math.sin(self.phase2 + x * 0.04) * 4.0
                back_wave.lineTo(x, y)
                x += 3
            back_wave.lineTo(rect.right() + 5, rect.bottom() + 5)
            back_wave.closeSubpath()

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(base_col.red(), base_col.green(), base_col.blue(), 140)))
            painter.drawPath(back_wave)

            # 4. Пузырьки
            painter.setPen(QPen(QColor(255, 255, 255, 140), 1))
            painter.setBrush(QBrush(QColor(base_col.red(), base_col.green(), base_col.blue(), 80)))
            for b in self.bubbles:
                if b['y'] >= surface_y:
                    painter.drawEllipse(QPoint(int(b['x']), int(b['y'])), int(b['r']), int(b['r']))

            # 5. Передняя волна
            front_wave = QPainterPath()
            front_wave.moveTo(rect.left() - 5, rect.bottom() + 5)
            front_wave.lineTo(rect.left() - 5, surface_y)

            x = rect.left() - 5
            while x <= rect.right() + 5:
                y = surface_y + math.sin(self.phase1 + x * 0.06) * 3.5
                front_wave.lineTo(x, y)
                x += 3
            front_wave.lineTo(rect.right() + 5, rect.bottom() + 5)
            front_wave.closeSubpath()

            grad = QLinearGradient(0, surface_y, 0, rect.bottom())
            grad.setColorAt(0.0, QColor(base_col.red(), base_col.green(), base_col.blue(), 230))
            grad.setColorAt(1.0, QColor(max(0, base_col.red() - 40), max(0, base_col.green() - 40), max(0, base_col.blue() - 40), 250))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawPath(front_wave)

            # 6. Оверлей
            painter.setClipping(False)
            self._draw_glass_overlay(painter, rect, w, h, base_col)
        finally:
            painter.end()

    def _draw_glass_overlay(self, painter, rect, w, h, base_col):
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1.5))
        painter.drawLine(int(rect.left() + 6), int(rect.top() + 8), int(rect.left() + 6), int(rect.bottom() - 8))

        pct_text = f"{int(self.fill_level * 100)}%"
        bw, bh = min(48.0, w - 12), 22.0
        badge_rect = QRectF(w / 2 - bw / 2, h / 2 - bh / 2, bw, bh)

        painter.setPen(QPen(QColor(base_col.red(), base_col.green(), base_col.blue(), 140), 1))
        painter.setBrush(QBrush(QColor(11, 15, 25, 230)))
        painter.drawRoundedRect(badge_rect, 6, 6)

        painter.setPen(QPen(QColor("#F8FAFC")))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, pct_text)


class ToastNotification(QWidget):
    """Анимированное всплывающее уведомление."""

    def __init__(self, parent: QWidget, message: str, level: str = "INFO"):
        super().__init__(parent)
        self.setWindowFlags(Qt.SubWindow | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        border_card = QFrame()
        color_map = {"INFO": ("#00F2FE", "ℹ️"), "SUCCESS": ("#10B981", "✅"), "ERROR": ("#EF4444", "❌")}
        border_color, icon = color_map.get(level.upper(), ("#00F2FE", "ℹ️"))

        border_card.setStyleSheet(f"QFrame {{ background-color: rgba(15, 23, 42, 0.9); border: 1.5px solid {border_color}; border-radius: 10px; }}")
        card_layout = QHBoxLayout(border_card)
        card_layout.setContentsMargins(16, 12, 16, 12)

        lbl = QLabel(f"{icon}  {message}")
        lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl.setStyleSheet("color: #F8FAFC; background: transparent;")

        card_layout.addWidget(lbl)
        layout.addWidget(border_card)
        self.adjustSize()

        p_rect = parent.rect()
        margin = 20
        start_x = p_rect.width() - self.width() - margin
        start_y = p_rect.height() + 20
        end_y = p_rect.height() - self.height() - margin

        self.move(start_x, start_y)

        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(350)
        self.anim.setStartValue(QPoint(start_x, start_y))
        self.anim.setEndValue(QPoint(start_x, end_y))
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.start()

        QTimer.singleShot(3400, self.fadeOut)

    def fadeOut(self):
        p_rect = self.parent().rect()
        end_y = p_rect.height() + 30
        self.anim_out = QPropertyAnimation(self, b"pos")
        self.anim_out.setDuration(250)
        self.anim_out.setStartValue(self.pos())
        self.anim_out.setEndValue(QPoint(self.x(), end_y))
        self.anim_out.setEasingCurve(QEasingCurve.InCubic)
        self.anim_out.finished.connect(self.close)
        self.anim_out.start()

    @staticmethod
    def show_toast(parent: QWidget, message: str, level: str = "INFO"):
        toast = ToastNotification(parent, message, level)
        toast.show()