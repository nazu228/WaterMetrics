# ui/interactive_modules.py
"""
Модуль интерактивных компонентов UI для WaterMetrics.
Стиль: Dark Tech Azure Glassmorphism.
"""

import math
import random
from typing import List, Dict

from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, QRectF, QEvent, Signal
from PySide6.QtGui import QFont, QColor, QPainter, QPainterPath, QPen, QBrush, QDragEnterEvent, QDropEvent, QLinearGradient


class HoverGlassCard(QFrame):
    """Стеклянная карточка с подсветкой границ при наведении."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassCard")

    def enterEvent(self, event: QEvent):
        self.setStyleSheet("""
            QFrame#GlassCard {
                background-color: #172033;
                border: 1.5px solid #00F2FE;
                border-radius: 12px;
            }
        """)
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        self.setStyleSheet("""
            QFrame#GlassCard {
                background-color: #111827;
                border: 1px solid rgba(0, 242, 254, 0.25);
                border-radius: 12px;
            }
        """)
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
        self.init_ui()

    def init_ui(self):
        self.setObjectName("GlassCard")
        self.setMinimumSize(200, 95)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)

        self.lbl_title = QLabel(f"<b>{self.title}</b>")
        self.lbl_title.setStyleSheet("color: #00F2FE; font-size: 13px; background: transparent;")

        self.lbl_status = QLabel(self.placeholder)
        self.lbl_status.setStyleSheet("color: #94A3B8; font-size: 12px; background: transparent;")

        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_browse = QPushButton("Обзор...")
        self.btn_browse.setObjectName("SecondaryButton")
        self.btn_browse.clicked.connect(self._open_file_dialog)
        btn_box.addWidget(self.btn_browse)

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_status)
        layout.addLayout(btn_box)

    def mousePressEvent(self, event):
        """Клик по любой области карточки вызывает окно выбора файла."""
        if event.button() == Qt.LeftButton:
            # Если кликнули не по самой кнопке (у кнопки свой сигнал clicked)
            child = self.childAt(event.pos())
            if not isinstance(child, QPushButton):
                self._open_file_dialog()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            if any(url.toLocalFile().endswith(('.xlsx', '.xls')) for url in event.mimeData().urls()):
                event.acceptProposedAction()
                self.setStyleSheet("""
                    QFrame#GlassCard {
                        background-color: rgba(0, 242, 254, 0.12);
                        border: 2px dashed #00F2FE;
                        border-radius: 12px;
                    }
                """)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QFrame#GlassCard {
                background-color: #111827;
                border: 1px solid rgba(0, 242, 254, 0.25);
                border-radius: 12px;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        self.dragLeaveEvent(event)
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.endswith(('.xlsx', '.xls')):
                self.set_file_path(path)
                break

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, f"Выберите {self.title}", "", "Excel (*.xlsx *.xls)")
        if path:
            self.set_file_path(path)

    def set_file_path(self, path: str):
        self.file_path = path
        filename = path.replace('\\', '/').split('/')[-1]
        self.lbl_status.setText(f"✓ Выбран: <b>{filename}</b>")
        self.lbl_status.setStyleSheet("color: #10B981; font-size: 12px; font-weight: bold; background: transparent;")
        self.file_dropped.emit(path)


class WaterGaugeWidget(QWidget):
    """Оптимизированный гидравлический индикатор с Event-driven анимацией и 0% CPU в idle."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(110, 140)
        
        self.fill_level = 0.0
        self.target_level = 0.0
        self.phase1 = 0.0
        self.phase2 = 1.5

        self.bubbles = []
        self._init_bubbles()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_frame)
        # В режиме простоя таймер выключен

    def _init_bubbles(self):
        for _ in range(10):
            self.bubbles.append({
                'x': random.uniform(15, 85),
                'y': random.uniform(20, 120),
                'r': random.uniform(1.5, 3.0),
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

        w_height = (self.height() - 20) * self.fill_level
        water_surface_y = (self.height() - 10) - w_height

        for b in self.bubbles:
            b['y'] -= b['speed']
            b['wobble'] += 0.05
            b['x'] += math.sin(b['wobble']) * 0.3

            if b['y'] < water_surface_y or b['y'] < 15:
                b['y'] = self.height() - 15
                b['x'] = random.uniform(15, max(20, self.width() - 15))

        self.update()

    def paintEvent(self, event):
        painter = QPainter()
        if not painter.begin(self):
            return

        try:
            painter.setRenderHint(QPainter.Antialiasing)
            w, h = self.width(), self.height()
            rect = QRectF(8, 8, w - 16, h - 16)

            # 1. Задний фон колбы
            painter.setPen(QPen(QColor(0, 242, 254, 60), 1.5))
            painter.setBrush(QBrush(QColor(15, 23, 42, 220)))
            painter.drawRoundedRect(rect, 14, 14)

            if self.fill_level <= 0.01:
                self._draw_glass_overlay(painter, rect, w, h)
                return

            # 2. Клиппинг воды
            clip_path = QPainterPath()
            clip_path.addRoundedRect(rect, 14, 14)
            painter.setClipPath(clip_path)

            water_height = rect.height() * self.fill_level
            surface_y = rect.bottom() - water_height

            # 3. Задняя волна
            back_wave = QPainterPath()
            back_wave.moveTo(rect.left() - 5, rect.bottom() + 10)
            back_wave.lineTo(rect.left() - 5, surface_y)

            x = rect.left() - 5
            while x <= rect.right() + 5:
                y = surface_y + math.sin(self.phase2 + x * 0.04) * 5.0
                back_wave.lineTo(x, y)
                x += 3
            back_wave.lineTo(rect.right() + 5, rect.bottom() + 10)
            back_wave.closeSubpath()

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(2, 128, 144, 160)))
            painter.drawPath(back_wave)

            # 4. Пузырьки
            painter.setPen(QPen(QColor(255, 255, 255, 140), 1))
            painter.setBrush(QBrush(QColor(0, 242, 254, 80)))
            for b in self.bubbles:
                if b['y'] >= surface_y:
                    painter.drawEllipse(QPoint(int(b['x']), int(b['y'])), int(b['r']), int(b['r']))

            # 5. Передняя волна
            front_wave = QPainterPath()
            front_wave.moveTo(rect.left() - 5, rect.bottom() + 10)
            front_wave.lineTo(rect.left() - 5, surface_y)

            x = rect.left() - 5
            while x <= rect.right() + 5:
                y = surface_y + math.sin(self.phase1 + x * 0.06) * 4.0
                front_wave.lineTo(x, y)
                x += 3
            front_wave.lineTo(rect.right() + 5, rect.bottom() + 10)
            front_wave.closeSubpath()

            grad = QLinearGradient(0, surface_y, 0, rect.bottom())
            grad.setColorAt(0.0, QColor(0, 242, 254, 220))
            grad.setColorAt(1.0, QColor(0, 168, 150, 240))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawPath(front_wave)

            # 6. Текст
            painter.setClipping(False)
            self._draw_glass_overlay(painter, rect, w, h)
        finally:
            painter.end()

    def _draw_glass_overlay(self, painter, rect, w, h):
        painter.setPen(QPen(QColor(255, 255, 255, 30), 1.5))
        painter.drawLine(int(rect.left() + 6), int(rect.top() + 10), int(rect.left() + 6), int(rect.bottom() - 10))

        pct_text = f"{int(self.fill_level * 100)}%"
        badge_rect = QRectF(w / 2 - 26, h / 2 - 13, 52, 26)

        painter.setPen(QPen(QColor(0, 242, 254, 120), 1))
        painter.setBrush(QBrush(QColor(11, 15, 25, 230)))
        painter.drawRoundedRect(badge_rect, 6, 6)

        painter.setPen(QPen(QColor("#F8FAFC")))
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold))
        painter.drawText(badge_rect, Qt.AlignCenter, pct_text)


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

        border_card.setStyleSheet(f"QFrame {{ background-color: #0F172A; border: 1.5px solid {border_color}; border-radius: 10px; }}")
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