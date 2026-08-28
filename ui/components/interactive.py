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
    QPushButton, QFileDialog, QSizePolicy
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
        self.setMinimumSize(120, 52)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.box_layout = QVBoxLayout(self)
        self.box_layout.setContentsMargins(8, 4, 8, 4)
        self.box_layout.setSpacing(2)
        self.box_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.icon_badge = GlassIconWidget("folder", size=QSize(24, 24))
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
        if theme_name:
            self._current_theme_name = theme_name
        curr_theme = getattr(self, '_current_theme_name', None) or ThemeManager.get_current_theme_name()
        accent = ThemeManager.get_current_accent_color(curr_theme)
        is_light = curr_theme in ("Pearl Light", "Как дома")
        
        if curr_theme == "Как дома":
            title_color = "#0A246A"
        elif curr_theme == "Pearl Light":
            title_color = "#028090"
        elif curr_theme == "Deep Violet Glass":
            title_color = "#D8B4FE"
        else:
            title_color = accent

        sub_color = "#334155" if is_light else "#CBD5E1"
        status_loaded_color = "#059669" if is_light else "#34D399"
        
        if hasattr(self, 'icon_badge'):
            self.icon_badge.set_color(title_color)

        f_size = "12px" if self.height() < 65 else ("13px" if self.height() < 90 else "14px")
        s_size = "11.5px" if self.height() < 65 else ("12.5px" if self.height() < 90 else "13px")

        self.lbl_title.setStyleSheet(f"color: {title_color}; font-size: {f_size}; font-weight: 800; background: transparent;")
        if not self.file_path:
            self.lbl_status.setStyleSheet(f"color: {sub_color}; font-size: {s_size}; font-weight: 600; background: transparent;")
        else:
            self.lbl_status.setStyleSheet(f"color: {status_loaded_color}; font-size: {s_size}; font-weight: 700; background: transparent;")

        theme_configs = {
            "Dark Tech Azure": {
                "bg_default": "rgba(15, 23, 42, 0.70)",
                "bg_hover": "rgba(18, 28, 50, 0.85)",
                "bg_linked": "rgba(0, 242, 254, 0.10)",
                "bg_drag": "rgba(0, 242, 254, 0.15)",
                "border": "rgba(0, 242, 254, 0.35)",
                "accent": "#00F2FE",
                "radius": "10px"
            },
            "Pearl Light": {
                "bg_default": "rgba(255, 255, 255, 0.90)",
                "bg_hover": "#FFFFFF",
                "bg_linked": "rgba(2, 128, 144, 0.08)",
                "bg_drag": "rgba(2, 128, 144, 0.14)",
                "border": "#028090",
                "accent": "#028090",
                "radius": "10px"
            },
            "Cyberpunk Neon": {
                "bg_default": "rgba(36, 5, 54, 0.70)",
                "bg_hover": "rgba(48, 7, 72, 0.85)",
                "bg_linked": "rgba(255, 0, 127, 0.12)",
                "bg_drag": "rgba(255, 0, 127, 0.18)",
                "border": "rgba(255, 0, 127, 0.40)",
                "accent": "#FF007F",
                "radius": "10px"
            },
            "Emerald Cyber": {
                "bg_default": "rgba(6, 38, 24, 0.70)",
                "bg_hover": "rgba(9, 51, 32, 0.85)",
                "bg_linked": "rgba(16, 185, 129, 0.10)",
                "bg_drag": "rgba(16, 185, 129, 0.15)",
                "border": "rgba(16, 185, 129, 0.40)",
                "accent": "#10B981",
                "radius": "10px"
            },
            "Deep Violet Glass": {
                "bg_default": "rgba(24, 10, 56, 0.70)",
                "bg_hover": "rgba(37, 15, 82, 0.85)",
                "bg_linked": "rgba(168, 85, 247, 0.12)",
                "bg_drag": "rgba(168, 85, 247, 0.18)",
                "border": "rgba(168, 85, 247, 0.40)",
                "accent": "#A855F7",
                "radius": "10px"
            },
            "Как дома": {
                "bg_default": "#FFFFFF",
                "bg_hover": "#F8FAFC",
                "bg_linked": "#FFFFFF",
                "bg_drag": "#F0F4F8",
                "border": "#7F9DB9",
                "accent": "#0A246A",
                "radius": "4px"
            }
        }
        cfg = theme_configs.get(curr_theme, theme_configs["Dark Tech Azure"])

        self.setStyleSheet(f"""
            QFrame#GlassCard {{
                background: {cfg["bg_default"]};
                border: 1.5px dashed {cfg["border"]};
                border-radius: {cfg["radius"]};
            }}
            QFrame#GlassCard:hover, QFrame#GlassCard[hover="true"] {{
                background: {cfg["bg_hover"]};
                border: 1.5px dashed {cfg["accent"]};
                border-radius: {cfg["radius"]};
            }}
            QFrame#GlassCard[state="linked"] {{
                background: {cfg["bg_linked"]};
                border: 1.5px solid {cfg["accent"]};
                border-radius: {cfg["radius"]};
            }}
            QFrame#GlassCard[state="warning"] {{
                background: rgba(239, 68, 68, 0.10);
                border: 1.5px solid #EF4444;
                border-radius: {cfg["radius"]};
            }}
            QFrame#GlassCard[drag="true"] {{
                background: {cfg["bg_drag"]};
                border: 2px dashed {cfg["accent"]};
                border-radius: {cfg["radius"]};
            }}
        """)

    def set_compact_mode(self, is_compact: bool):
        """Адаптивный компактный режим для малых размеров карточек."""
        self.is_compact = is_compact
        if is_compact:
            self.icon_badge.setVisible(False)
            self.setMinimumHeight(46)
            self.box_layout.setContentsMargins(6, 3, 6, 3)
            self.box_layout.setSpacing(1)
            self.lbl_status.setVisible(True)
        else:
            self.setMinimumHeight(52)
            self.box_layout.setContentsMargins(8, 4, 8, 4)
            self.box_layout.setSpacing(2)
            self._update_responsive_view()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_responsive_view()
        self._update_elided_status_text()

    def _update_responsive_view(self):
        h = self.height()
        if self.is_compact or h < 74:
            self.icon_badge.setVisible(False)
            self.box_layout.setContentsMargins(6, 3, 6, 3)
            self.box_layout.setSpacing(1)
        else:
            self.icon_badge.setVisible(True)
            self.icon_badge.setFixedSize(24, 24)
            self.box_layout.setContentsMargins(8, 4, 8, 4)
            self.box_layout.setSpacing(2)
        self._update_theme_colors()

    def _get_title_color(self) -> str:
        curr_theme = ThemeManager.get_current_theme_name()
        accent = ThemeManager.get_current_accent_color()
        if curr_theme == "Как дома":
            return "#0A246A"
        elif curr_theme == "Pearl Light":
            return "#028090"
        return accent

    def _update_elided_status_text(self):
        max_w = max(50, self.width() - 16)
        if not self.file_path or not os.path.exists(self.file_path):
            fm = self.lbl_status.fontMetrics()
            elided_ph = fm.elidedText(self.placeholder, Qt.TextElideMode.ElideMiddle, max_w)
            self.lbl_status.setText(elided_ph)
            self.setToolTip(f"{self.title}\n{self.placeholder}")
            return

        filename = os.path.basename(self.file_path)
        fm = self.lbl_status.fontMetrics()
        elided_filename = fm.elidedText(filename, Qt.TextElideMode.ElideMiddle, max_w)
        
        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        size_color = "#64748B" if is_light else "#94A3B8"

        try:
            sz_bytes = os.path.getsize(self.file_path)
            sz_str = f"{sz_bytes / 1024:.1f} KB" if sz_bytes < 1024 * 1024 else f"{sz_bytes / (1024 * 1024):.2f} MB"
            meta_info = f" <span style='color: {size_color}; font-size: 11px; font-weight: normal;'>({sz_str})</span>"
        except Exception:
            meta_info = ""

        if self.height() < 70:
            self.lbl_status.setText(f"✓ <b>{elided_filename}</b>")
        else:
            self.lbl_status.setText(f"✓ <b>{elided_filename}</b>{meta_info}")
        self.setToolTip(f"{self.title}\n{self.file_path}")

    def set_file_path(self, path: str, notify: bool = True):
        prev_path = self.file_path
        self.file_path = path
        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        status_color = "#059669" if is_light else "#10B981"

        if path and os.path.exists(path):
            self._update_elided_status_text()
            self.lbl_status.setStyleSheet(f"color: {status_color}; font-size: 12.5px; font-weight: bold; background: transparent;")
        else:
            self._update_elided_status_text()
            self._update_theme_colors()

        if self.is_compact and self.file_path:
            self.lbl_status.setVisible(True)
        if notify and (not prev_path or os.path.normpath(prev_path) != os.path.normpath(path)):
            self.file_dropped.emit(path)

    def mousePressEvent(self, event):
        """Клик по любой области карточки вызывает окно выбора файла."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_file_dialog()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            if any(url.toLocalFile().endswith(('.xlsx', '.xls')) or os.path.isdir(url.toLocalFile()) for url in event.mimeData().urls()):
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
            if os.path.isdir(path):
                xlsx_files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(('.xlsx', '.xls')) and not f.startswith('~$') and not any(ex in f.lower() for ex in ['сопроводит', 'акт', 'аркус'])]
                if xlsx_files:
                    self.set_file_path(xlsx_files[0], notify=True)
                else:
                    self.set_file_path(path, notify=True)
                break
            elif path.endswith(('.xlsx', '.xls')):
                self.set_file_path(path, notify=True)
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
        curr_theme = getattr(self, '_current_theme_name', None) or ThemeManager.get_current_theme_name()
        accent = ThemeManager.get_current_accent_color(curr_theme)
        is_light = curr_theme in ("Pearl Light", "Как дома")
        if message:
            self.lbl_status.setText(message)
            if state == "linked":
                acc_txt = "#0A246A" if curr_theme == "Как дома" else ("#028090" if is_light else accent)
                self.lbl_status.setStyleSheet(f"color: {acc_txt}; font-size: 12.5px; font-weight: bold; background: transparent;")
            elif state == "warning":
                self.lbl_status.setStyleSheet("color: #EF4444; font-size: 12.5px; font-weight: bold; background: transparent;")
        elif not self.file_path:
            self.lbl_status.setText(self.placeholder)
            sub_col = "#334155" if is_light else "#94A3B8"
            self.lbl_status.setStyleSheet(f"color: {sub_col}; font-size: 12.5px; background: transparent;")


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
        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        color_map = {"INFO": ("#00F2FE", "ℹ️"), "SUCCESS": ("#10B981", "✅"), "ERROR": ("#EF4444", "❌")}
        border_color, icon = color_map.get(level.upper(), ("#00F2FE", "ℹ️"))
        if is_light:
            bg_col = "rgba(255, 255, 255, 0.96)" if curr_theme == "Как дома" else "rgba(248, 250, 252, 0.95)"
            txt_col = "#000000" if curr_theme == "Как дома" else "#0F172A"
        else:
            bg_col = "rgba(15, 23, 42, 0.9)"
            txt_col = "#F8FAFC"

        border_card.setStyleSheet(f"QFrame {{ background-color: {bg_col}; border: 1.5px solid {border_color}; border-radius: 10px; }}")
        card_layout = QHBoxLayout(border_card)
        card_layout.setContentsMargins(16, 12, 16, 12)

        lbl = QLabel(f"{icon}  {message}")
        lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl.setStyleSheet(f"color: {txt_col}; background: transparent;")

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