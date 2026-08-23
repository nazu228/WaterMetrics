# create_structure.py
import os

FILES = {
    "ui/styles.py": '''# ui/styles.py
"""
Единая дизайн-система "Dark Tech Azure Glassmorphism".
Высокий контраст, глубокие темные фоны и лазурные акценты.
"""

DARK_AZURE_QSS = """
/* ============================================================================
   GLOBAL WINDOW & PAGES
   ============================================================================ */
QMainWindow, QWidget#MainContainer {
    background-color: #0B0F19;
    color: #F8FAFC;
    font-family: "Segoe UI", "Inter", sans-serif;
}

QWidget {
    font-family: "Segoe UI", "Inter", sans-serif;
    color: #F8FAFC;
}

/* Непрозрачный фон для всех страниц (Исключает просвечивание в QStackedWidget) */
QWidget#DashboardPage, QWidget#NormsPage, QWidget#LogsPage, QWidget#AutoTestsPage, QWidget#AboutPage {
    background-color: #0B0F19;
}

/* ============================================================================
   GLASS CARDS & PANELS
   ============================================================================ */
QFrame#GlassCard {
    background-color: #111827;
    border: 1px solid rgba(0, 242, 254, 0.25);
    border-radius: 12px;
}

QFrame#SidebarPanel {
    background-color: #070A12;
    border-right: 1px solid rgba(0, 242, 254, 0.15);
}

/* ============================================================================
   LABELS & TYPOGRAPHY
   ============================================================================ */
QLabel {
    color: #F8FAFC;
    font-size: 13px;
}

QLabel#PageTitle {
    color: #F8FAFC;
    font-size: 22px;
    font-weight: 700;
}

QLabel#SectionTitle {
    color: #00F2FE;
    font-size: 15px;
    font-weight: 600;
}

QLabel#FieldLabel {
    color: #94A3B8;
    font-size: 13px;
    font-weight: 600;
}

/* ============================================================================
   INPUT FIELDS
   ============================================================================ */
QLineEdit, QComboBox {
    background-color: #0F172A;
    border: 1.5px solid rgba(148, 163, 184, 0.3);
    border-radius: 8px;
    padding: 8px 12px;
    color: #F8FAFC;
    font-size: 13px;
    selection-background-color: #028090;
    selection-color: #FFFFFF;
}

QLineEdit:focus, QComboBox:focus {
    border: 1.5px solid #00F2FE;
    background-color: #1E293B;
}

QComboBox QAbstractItemView {
    background-color: #0F172A;
    border: 1px solid #00F2FE;
    selection-background-color: #028090;
    color: #F8FAFC;
    outline: none;
}

/* ============================================================================
   BUTTONS
   ============================================================================ */
QPushButton#PrimaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #028090, stop:0.5 #00A896, stop:1 #00F2FE);
    color: #0B0F19;
    font-weight: 700;
    font-size: 13px;
    border-radius: 8px;
    padding: 9px 18px;
    border: none;
    min-height: 24px;
}
QPushButton#PrimaryButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00A896, stop:1 #00F2FE);
}
QPushButton#PrimaryButton:disabled {
    background: #1E293B;
    color: #64748B;
}

QPushButton#SecondaryButton {
    background-color: #1E293B;
    color: #F8FAFC;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 8px;
    padding: 7px 14px;
    min-height: 20px;
}
QPushButton#SecondaryButton:hover {
    background-color: #334155;
    border-color: #00F2FE;
    color: #00F2FE;
}

QPushButton#AccentButton {
    background-color: rgba(0, 242, 254, 0.15);
    color: #00F2FE;
    font-weight: 700;
    font-size: 13px;
    border: 1.5px solid rgba(0, 242, 254, 0.5);
    border-radius: 8px;
    padding: 8px 16px;
    min-height: 22px;
}
QPushButton#AccentButton:hover {
    background-color: rgba(0, 242, 254, 0.28);
    border-color: #00F2FE;
}

QPushButton#DangerButton {
    background-color: rgba(239, 68, 68, 0.2);
    color: #F87171;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-radius: 8px;
    padding: 7px 14px;
    min-height: 20px;
}
QPushButton#DangerButton:hover {
    background-color: rgba(239, 68, 68, 0.35);
    border-color: #EF4444;
}

QPushButton.navBtn {
    background-color: transparent;
    color: #94A3B8;
    text-align: left;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    border: none;
}
QPushButton.navBtn:hover {
    background-color: rgba(255, 255, 255, 0.06);
    color: #F8FAFC;
}
QPushButton.navBtn:checked {
    background-color: rgba(0, 242, 254, 0.15);
    color: #00F2FE;
    font-weight: 700;
    border-left: 3px solid #00F2FE;
}

/* ============================================================================
   TABLES, LOGS, STATUSBAR
   ============================================================================ */
QTableWidget {
    background-color: #0F172A;
    color: #F8FAFC;
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 8px;
    gridline-color: rgba(148, 163, 184, 0.1);
}
QTableWidget::item { padding: 6px; color: #E2E8F0; }
QTableWidget::item:selected { background-color: rgba(2, 128, 144, 0.5); color: #00F2FE; }

QHeaderView::section {
    background-color: #070A12;
    color: #00F2FE;
    padding: 8px;
    font-weight: 600;
    font-size: 12px;
    border: none;
    border-bottom: 1.5px solid rgba(0, 242, 254, 0.3);
}

QTextEdit#LogViewer {
    background-color: #0F172A;
    color: #F8FAFC;
    border-radius: 8px;
    font-family: "Consolas", monospace;
    font-size: 12px;
    padding: 10px;
    border: 1px solid rgba(148, 163, 184, 0.2);
}

QDialog {
    background-color: #0B0F19;
    color: #F8FAFC;
}

QStatusBar {
    background-color: #070A12;
    border-top: 1px solid rgba(148, 163, 184, 0.15);
    color: #94A3B8;
}

QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #1E293B;
    max-height: 8px;
}
QProgressBar::chunk {
    background-color: #00F2FE;
    border-radius: 4px;
}
"""

BEACH_QSS = DARK_AZURE_QSS
''',

    "ui/components/__init__.py": "",

    "ui/components/interactive.py": '''# ui/components/interactive.py
import math
import random
from typing import List, Dict

from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QTimer, QRectF, QEvent, Signal
from PySide6.QtGui import QFont, QColor, QPainter, QPainterPath, QPen, QBrush, QDragEnterEvent, QDropEvent, QLinearGradient

class HoverGlassCard(QFrame):
    """Стеклянная карточка с изменением границ при наведении (без QGraphicsEffect)."""

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


class WaterGaugeWidget(QWidget):
    """Оптимизированный гидравлический индикатор с безопасным QPainter контекстом."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(110, 150)
        
        self.fill_level = 0.0
        self.target_level = 0.0
        self.phase1 = 0.0
        self.phase2 = 1.5

        self.bubbles = []
        self._init_bubbles()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_frame)
        self.timer.start(33)

    def _init_bubbles(self):
        for _ in range(10):
            self.bubbles.append({
                'x': random.uniform(15, 85),
                'y': random.uniform(20, 130),
                'r': random.uniform(1.5, 3.0),
                'speed': random.uniform(0.6, 1.5),
                'wobble': random.uniform(0, 6.28)
            })

    def set_level(self, pct: float):
        self.target_level = max(0.0, min(1.0, pct))

    def _animate_frame(self):
        self.phase1 += 0.08
        self.phase2 += 0.05

        if abs(self.fill_level - self.target_level) > 0.001:
            self.fill_level += (self.target_level - self.fill_level) * 0.06

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


class ExcelDropZone(QFrame):
    file_dropped = Signal(str)

    def __init__(self, title: str, placeholder: str = "Перетащите .xlsx файл сюда", parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.file_path = ""
        self.title = title
        self.placeholder = placeholder
        self.init_ui()

    def init_ui(self):
        self.setObjectName("GlassCard")
        self.setMinimumHeight(90)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)

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
        filename = path.replace('\\\\', '/').split('/')[-1]
        self.lbl_status.setText(f"✓ Выбран: <b>{filename}</b>")
        self.lbl_status.setStyleSheet("color: #10B981; font-size: 12px; font-weight: bold; background: transparent;")
        self.file_dropped.emit(path)


class ToastNotification(QWidget):
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
''',

    "ui/dashboard_page.py": '''# ui/dashboard_page.py
import os
import sys
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui.components.interactive import HoverGlassCard, ExcelDropZone, WaterGaugeWidget, ToastNotification

class MainDashboardPage(QWidget):
    def __init__(self, main_win):
        super().__init__()
        self.main_win = main_win
        self.setObjectName("DashboardPage")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🛠 Основная панель расчетов", objectName="PageTitle")
        layout.addWidget(title)

        # Выбор файлов с помощью Drag and Drop зон
        card_files = HoverGlassCard()
        grid_f = QGridLayout(card_files)
        grid_f.setContentsMargins(16, 16, 16, 16)
        grid_f.setSpacing(12)

        self.drop_tpl = ExcelDropZone("Файл шаблона (.xlsx)", "Перетащите шаблон прошлого месяца...")
        self.drop_arc = ExcelDropZone("Файл Аркус (.xlsx)", "Перетащите файл Аркус текущего месяца...")
        self.drop_tpl.file_dropped.connect(self._on_template_selected)

        grid_f.addWidget(self.drop_tpl, 0, 0)
        grid_f.addWidget(self.drop_arc, 0, 1)

        save_box = QHBoxLayout()
        save_box.addWidget(QLabel("<b>Сохранить в:</b>", objectName="FieldLabel"))
        self.txt_save = QLineEdit(placeholderText="Путь сохранения результата...")
        save_box.addWidget(self.txt_save, 1)

        btn_repl = QPushButton("🔄 Замена счетчиков (Мастер)", objectName="AccentButton")
        btn_repl.setFixedHeight(38)
        btn_repl.clicked.connect(self.main_win.open_replacement_dialog)

        grid_f.addLayout(save_box, 1, 0, 1, 2)
        grid_f.addWidget(btn_repl, 2, 0, 1, 2)

        layout.addWidget(card_files)

        # Индикатор WaterGauge и Параметры
        card_middle = HoverGlassCard()
        grid_m = QGridLayout(card_middle)
        grid_m.setContentsMargins(16, 16, 16, 16)

        grid_n = QGridLayout()
        grid_n.addWidget(QLabel("Цель ХВС (м³):", objectName="FieldLabel"), 0, 0)
        self.txt_cold = QLineEdit("0.0")
        grid_n.addWidget(self.txt_cold, 0, 1)

        grid_n.addWidget(QLabel("Цель ГВС (м³):", objectName="FieldLabel"), 0, 2)
        self.txt_hot = QLineEdit("0.0")
        grid_n.addWidget(self.txt_hot, 0, 3)

        grid_n.addWidget(QLabel("Коррекция ХВС:", objectName="FieldLabel"), 1, 0)
        self.txt_corr = QLineEdit("0")
        grid_n.addWidget(self.txt_corr, 1, 1)

        self.water_gauge = WaterGaugeWidget()

        grid_m.addLayout(grid_n, 0, 0)
        grid_m.addWidget(self.water_gauge, 0, 1)

        layout.addWidget(card_middle)

        # История созданных файлов
        card_hist = HoverGlassCard()
        layout_h = QVBoxLayout(card_hist)
        layout_h.setContentsMargins(16, 16, 16, 16)

        lbl_h = QLabel("История созданных файлов", objectName="SectionTitle")
        layout_h.addWidget(lbl_h)

        self.table_hist = QTableWidget(0, 2)
        self.table_hist.setHorizontalHeaderLabels(["Имя файла", "Полный путь"])
        self.table_hist.horizontalHeader().setFixedHeight(32)
        self.table_hist.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table_hist.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout_h.addWidget(self.table_hist)

        h_btns = QHBoxLayout()
        btn_open = QPushButton("📂 Открыть файл", objectName="SecondaryButton")
        btn_open.clicked.connect(self.open_file)
        btn_rem = QPushButton("🗑 Удалить", objectName="DangerButton")
        btn_rem.clicked.connect(self.remove_file)
        btn_clr = QPushButton("🧹 Очистить", objectName="SecondaryButton")
        btn_clr.clicked.connect(self.clear_file_list)

        h_btns.addWidget(btn_open)
        h_btns.addWidget(btn_rem)
        h_btns.addWidget(btn_clr)
        layout_h.addLayout(h_btns)

        layout.addWidget(card_hist, 1)

        self.btn_run = QPushButton("🚀 Сформировать файл", objectName="PrimaryButton")
        self.btn_run.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.btn_run.setFixedHeight(45)
        self.btn_run.clicked.connect(self.main_win.run_calculation)
        layout.addWidget(self.btn_run)

    def _on_template_selected(self, path: str):
        if not path:
            return
        try:
            suggested_name = self.main_win.excel_manager.parse_house_and_next_month(path)
            folder = os.path.dirname(path)
            self.txt_save.setText(os.path.join(folder, suggested_name))
        except Exception:
            folder = os.path.dirname(path)
            base_name = os.path.splitext(os.path.basename(path))[0]
            self.txt_save.setText(os.path.join(folder, f"{base_name}_готово.xlsx"))

    def add_history_entry(self, file_path: str):
        if not file_path or not os.path.exists(file_path):
            return

        for row in range(self.table_hist.rowCount()):
            item = self.table_hist.item(row, 1)
            if item and item.text() == file_path:
                return

        row_pos = self.table_hist.rowCount()
        self.table_hist.insertRow(row_pos)
        self.table_hist.setItem(row_pos, 0, QTableWidgetItem(os.path.basename(file_path)))
        self.table_hist.setItem(row_pos, 1, QTableWidgetItem(file_path))

    def open_file(self):
        row = self.table_hist.currentRow()
        if row >= 0:
            path = self.table_hist.item(row, 1).text()
            if os.path.exists(path):
                os.startfile(path) if sys.platform == 'win32' else subprocess.Popen(['xdg-open', path])
            else:
                ToastNotification.show_toast(self.main_win, "Файл не найден!", "ERROR")

    def remove_file(self):
        row = self.table_hist.currentRow()
        if row >= 0:
            self.table_hist.removeRow(row)

    def clear_file_list(self):
        self.table_hist.setRowCount(0)
''',

    "ui/norms_page.py": '''# ui/norms_page.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame, QGridLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Qt
from ui.components.interactive import HoverGlassCard

class NormsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NormsPage")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("📐 Настройка нормативов водопотребления", objectName="PageTitle")
        layout.addWidget(title)

        card = HoverGlassCard()
        grid = QGridLayout(card)
        grid.setContentsMargins(22, 22, 22, 22)
        grid.setSpacing(16)
        grid.setColumnStretch(1, 1)

        desc = QLabel(
            "Нормативы используются при распределении объемов воды для лицевых счетов,\\n"
            "начисляющих плату по нормативу при отсутствии показаний приборов учета."
        )
        desc.setStyleSheet("color: #94A3B8; font-size: 13px; line-height: 1.4;")
        grid.addWidget(desc, 0, 0, 1, 2)

        grid.addWidget(QLabel("Норматив ХВС (м³ на чел.):", objectName="FieldLabel"), 1, 0)
        self.txt_norm_cold = QLineEdit("4.04")
        self.txt_norm_cold.setMaximumWidth(200)
        grid.addWidget(self.txt_norm_cold, 1, 1)

        grid.addWidget(QLabel("Норматив ГВС (м³ на чел.):", objectName="FieldLabel"), 2, 0)
        self.txt_norm_hot = QLineEdit("2.65")
        self.txt_norm_hot.setMaximumWidth(200)
        grid.addWidget(self.txt_norm_hot, 2, 1)

        btn_save = QPushButton("💾 Сохранить нормативы", objectName="PrimaryButton")
        btn_save.setFixedWidth(220)
        grid.addWidget(btn_save, 3, 0, 1, 2)

        layout.addWidget(card)
        layout.addStretch()
''',

    "ui/logs_page.py": '''# ui/logs_page.py
from typing import List, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QTextEdit, QPushButton
from PySide6.QtCore import Qt
from ui.components.interactive import HoverGlassCard

class LogsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.raw_logs: List[Tuple[str, str]] = []
        self.setObjectName("LogsPage")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("📋 Терминал системных логов", objectName="PageTitle")
        layout.addWidget(title)

        card = HoverGlassCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)

        filters = QHBoxLayout()
        filters.setSpacing(16)

        self.chk_info = QCheckBox("INFO")
        self.chk_info.setChecked(True)
        self.chk_success = QCheckBox("SUCCESS")
        self.chk_success.setChecked(True)
        self.chk_error = QCheckBox("ERROR")
        self.chk_error.setChecked(True)

        self.chk_info.stateChanged.connect(self.refresh_display)
        self.chk_success.stateChanged.connect(self.refresh_display)
        self.chk_error.stateChanged.connect(self.refresh_display)

        btn_clear = QPushButton("🧹 Очистить консоль", objectName="SecondaryButton")
        btn_clear.clicked.connect(self.clear_logs)

        filters.addWidget(self.chk_info)
        filters.addWidget(self.chk_success)
        filters.addWidget(self.chk_error)
        filters.addStretch()
        filters.addWidget(btn_clear)

        card_layout.addLayout(filters)

        self.log_viewer = QTextEdit()
        self.log_viewer.setObjectName("LogViewer")
        self.log_viewer.setReadOnly(True)

        card_layout.addWidget(self.log_viewer, 1)
        layout.addWidget(card, 1)

    def append_log(self, msg: str, level: str):
        self.raw_logs.append((msg, level.upper()))
        self.render_line(msg, level.upper())

    def render_line(self, msg: str, level: str):
        colors = {"INFO": "#00F2FE", "SUCCESS": "#10B981", "ERROR": "#EF4444"}
        color = colors.get(level, "#F8FAFC")
        html = f'<span style="color: {color};"><b>[{level}]</b> {msg}</span>'
        self.log_viewer.append(html)

    def refresh_display(self):
        self.log_viewer.clear()
        for msg, level in self.raw_logs:
            if level == "INFO" and self.chk_info.isChecked():
                self.render_line(msg, level)
            elif level == "SUCCESS" and self.chk_success.isChecked():
                self.render_line(msg, level)
            elif level == "ERROR" and self.chk_error.isChecked():
                self.render_line(msg, level)

    def clear_logs(self):
        self.raw_logs.clear()
        self.log_viewer.clear()
''',

    "ui/test_tab.py": '''# ui/test_tab.py
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
from PySide6.QtCore import QThread, Signal, Qt
from ui.components.interactive import HoverGlassCard, ToastNotification

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class TestWorker(QThread):
    log_signal = Signal(str, str)
    finished_signal = Signal(bool, str)

    def __init__(self, excel_manager, target_dir: str):
        super().__init__()
        self.excel_manager = excel_manager
        self.target_dir = target_dir

    def run(self):
        try:
            self.log_signal.emit("Запуск процедуры автоматического тестирования...", "INFO")
            os.makedirs(self.target_dir, exist_ok=True)
            self.log_signal.emit("Выполнение сценария +100м³...", "INFO")
            QThread.msleep(500)
            self.log_signal.emit("Тест +100м³ завершен успешно.", "SUCCESS")
            self.log_signal.emit("Выполнение сценария -100м³...", "INFO")
            QThread.msleep(500)
            self.log_signal.emit("Тест -100м³ завершен успешно.", "SUCCESS")
            self.finished_signal.emit(True, "Все авто-тесты успешно пройдены!")
        except Exception as e:
            self.log_signal.emit(f"Ошибка авто-тестирования: {e}", "ERROR")
            self.finished_signal.emit(False, str(e))

class AutoTestsPage(QWidget):
    def __init__(self, main_win=None):
        super().__init__()
        self.main_win = main_win
        self.test_dir = os.path.join(BASE_DIR, "test_results")
        self.setObjectName("AutoTestsPage")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("🧪 Автоматическое тестирование алгоритмов", objectName="PageTitle")
        layout.addWidget(title)

        card = HoverGlassCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)

        ctrl_layout = QHBoxLayout()
        self.btn_run_tests = QPushButton("▶ Запустить Тест (+100m³ / -100m³)", objectName="PrimaryButton")
        self.btn_run_tests.clicked.connect(self.run_tests)

        btn_del = QPushButton("🗑 Удалить результаты", objectName="DangerButton")
        btn_del.clicked.connect(self.delete_results)

        ctrl_layout.addWidget(self.btn_run_tests)
        ctrl_layout.addWidget(btn_del)
        ctrl_layout.addStretch()

        card_layout.addLayout(ctrl_layout)

        self.test_log = QTextEdit()
        self.test_log.setObjectName("LogViewer")
        self.test_log.setReadOnly(True)

        card_layout.addWidget(self.test_log, 1)
        layout.addWidget(card, 1)

    def run_tests(self):
        self.btn_run_tests.setEnabled(False)
        self.test_log.append("<span style='color: #00F2FE;'><b>[TEST]</b> Запуск авто-тестов...</span>")
        excel_mgr = self.main_win.excel_manager if self.main_win else None
        self.worker = TestWorker(excel_mgr, self.test_dir)
        self.worker.log_signal.connect(self.log_from_worker)
        self.worker.finished_signal.connect(self.tests_finished)
        self.worker.start()

    def log_from_worker(self, msg: str, level: str):
        colors = {"INFO": "#00F2FE", "SUCCESS": "#10B981", "ERROR": "#EF4444"}
        c = colors.get(level.upper(), "#F8FAFC")
        self.test_log.append(f'<span style="color: {c};"><b>[{level}]</b> {msg}</span>')

    def tests_finished(self, success: bool, msg: str):
        self.btn_run_tests.setEnabled(True)
        parent_target = self.main_win if self.main_win else self
        if success:
            ToastNotification.show_toast(parent_target, "Авто-тесты успешно пройдены!", "SUCCESS")
        else:
            ToastNotification.show_toast(parent_target, f"Ошибка: {msg}", "ERROR")

    def delete_results(self):
        if os.path.exists(self.test_dir):
            for file in os.listdir(self.test_dir):
                fp = os.path.join(self.test_dir, file)
                if os.path.isfile(fp):
                    os.remove(fp)
            parent_target = self.main_win if self.main_win else self
            ToastNotification.show_toast(parent_target, "Папка результатов очищена", "INFO")
''',

    "ui/about_page.py": '''# ui/about_page.py
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QMovie
from ui.components.interactive import HoverGlassCard

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class BeachDialog(QDialog):
    def __init__(self, parent: QWidget, gif_path: str):
        super().__init__(parent)
        self.setWindowTitle("Морской Бриз - Отдых")
        self.setFixedSize(480, 360)

        layout = QVBoxLayout(self)
        lbl_gif = QLabel()
        lbl_gif.setAlignment(Qt.AlignCenter)

        if os.path.exists(gif_path):
            movie = QMovie(gif_path)
            lbl_gif.setMovie(movie)
            movie.start()
        else:
            lbl_gif.setText("🌴 Beach GIF file not found in assets/ 🌊")
            lbl_gif.setStyleSheet("font-size: 15px; color: #00F2FE; font-weight: bold;")

        layout.addWidget(lbl_gif)

class AboutPage(QWidget):
    def __init__(self, main_win=None):
        super().__init__()
        self.main_win = main_win
        self.setObjectName("AboutPage")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("ℹ️ О программе", objectName="PageTitle")
        layout.addWidget(title)

        card = HoverGlassCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(14)

        appName = QLabel("WaterMetrics Professional Edition")
        appName.setStyleSheet("font-size: 24px; font-weight: bold; color: #00F2FE;")

        sub = QLabel("Система автоматизированного расчета и распределения объемов водопотребления")
        sub.setStyleSheet("font-size: 14px; color: #94A3B8;")

        ver = QLabel("Версия: 2.0 (PySide6 Dark Tech Azure Edition)")
        ver.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 600;")

        btns = QHBoxLayout()
        btns.setSpacing(12)

        btn_donate = QPushButton("💳 Пожертвования", objectName="SecondaryButton")
        btn_donate.clicked.connect(self.show_donate)

        btn_beach = QPushButton("🏖 Морской Отдых", objectName="AccentButton")
        btn_beach.clicked.connect(self.show_beach)

        btns.addWidget(btn_donate)
        btns.addWidget(btn_beach)

        card_layout.addWidget(appName, alignment=Qt.AlignCenter)
        card_layout.addWidget(sub, alignment=Qt.AlignCenter)
        card_layout.addWidget(ver, alignment=Qt.AlignCenter)
        card_layout.addSpacing(10)
        card_layout.addLayout(btns)
        card_layout.addStretch()

        layout.addWidget(card, 1)

    def show_donate(self):
        card_number = "40817810807004134433"
        QMessageBox.information(
            self,
            "Пожертвования",
            f"Сбербанк\\nНомер карты: {card_number}\\n\\nБлагодарим за поддержку нашего проекта!"
        )

    def show_beach(self):
        gif_path = os.path.join(BASE_DIR, "assets", "beach.gif")
        dlg = BeachDialog(self, gif_path)
        dlg.exec()
''',

    "ui/dialogs/replacement_dialog.py": '''# ui/dialogs/replacement_dialog.py
import re
from typing import List, Dict, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QLabel,
    QLineEdit, QComboBox, QScrollArea, QPushButton, QMessageBox, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from models import ClosedMeterRecord, NewMeterRecord
from ui.components.interactive import ToastNotification

class MeterReplacementDialog(QDialog):
    def __init__(self, parent=None, apartments_data: Dict[str, List[Dict]] = None,
                 initial_closed: List[ClosedMeterRecord] = None,
                 initial_new: List[NewMeterRecord] = None):
        super().__init__(parent)
        self.setWindowTitle("Мастер замены счетчиков (ИПУ)")
        self.resize(720, 620)
        self.setModal(True)

        self.apts_data = apartments_data or {}
        self.closed_records = {(r.apartment, r.water_type, r.meter_num): r for r in (initial_closed or [])}
        self.new_records = {(r.apartment, r.water_type, r.meter_num): r for r in (initial_new or [])}

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        search_card = QFrame()
        search_card.setObjectName("GlassCard")
        sc_layout = QHBoxLayout(search_card)

        sc_layout.addWidget(QLabel("🔍 <b>Поиск квартиры:</b>"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Введите номер квартиры...")
        self.search_edit.textChanged.connect(self._on_search_changed)
        sc_layout.addWidget(self.search_edit)

        layout.addWidget(search_card)

        select_card = QFrame()
        select_card.setObjectName("GlassCard")
        sl_layout = QHBoxLayout(select_card)

        sl_layout.addWidget(QLabel("<b>Выбранное помещение:</b>"))
        self.apt_combo = QComboBox()
        self.apt_combo.currentTextChanged.connect(self._on_apt_selected)
        sl_layout.addWidget(self.apt_combo, 1)

        layout.addWidget(select_card)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.scroll_content = QWidget()
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setSpacing(10)
        self.scroll_area.setWidget(self.scroll_content)

        layout.addWidget(self.scroll_area, 1)

        footer = QHBoxLayout()
        self.lbl_info = QLabel("Оформлено замен: 0")
        self.lbl_info.setStyleSheet("color: #00F2FE; font-weight: bold; font-size: 13px;")
        footer.addWidget(self.lbl_info)
        footer.addStretch()

        btn_save = QPushButton("Применить и закрыть", objectName="PrimaryButton")
        btn_save.clicked.connect(self.accept)
        footer.addWidget(btn_save)

        layout.addLayout(footer)
        self.populate_apartments()

    def _get_apt_score(self, apt_name: str, query: str) -> Tuple[int, int, str]:
        q = query.strip().lower()
        apt_lower = str(apt_name).lower()
        nums = re.findall(r'\\d+', apt_lower)
        apt_num_str = nums[0] if nums else ""
        apt_num_val = int(apt_num_str) if apt_num_str else 999999

        if not q:
            return (0, apt_num_val, apt_lower)
        if q == apt_num_str or q == apt_lower:
            priority = 0
        elif apt_num_str.startswith(q):
            priority = 1
        elif q in apt_num_str:
            priority = 2
        elif q in apt_lower:
            priority = 3
        else:
            priority = 99
        return (priority, apt_num_val, apt_lower)

    def populate_apartments(self):
        sorted_apts = sorted(list(self.apts_data.keys()), key=lambda x: int(re.findall(r'\\d+', x)[0]) if re.findall(r'\\d+', x) else 999)
        self.apt_combo.blockSignals(True)
        self.apt_combo.clear()
        self.apt_combo.addItems(sorted_apts if sorted_apts else ["Нет доступных квартир"])
        self.apt_combo.blockSignals(False)
        if sorted_apts:
            self._on_apt_selected(sorted_apts[0])

    def _on_search_changed(self, query: str):
        if not query.strip():
            self.populate_apartments()
            return

        scored = []
        for apt in self.apts_data.keys():
            score = self._get_apt_score(apt, query)
            if score[0] < 99:
                scored.append((score, apt))

        scored.sort(key=lambda x: x[0])
        filtered = [item[1] for item in scored]

        self.apt_combo.blockSignals(True)
        self.apt_combo.clear()
        if filtered:
            self.apt_combo.addItems(filtered)
            self.apt_combo.blockSignals(False)
            self._on_apt_selected(filtered[0])

    def _clear_cards(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _on_apt_selected(self, apt_name: str):
        self._clear_cards()
        if apt_name not in self.apts_data:
            return

        for m in self.apts_data.get(apt_name, []):
            self.cards_layout.addWidget(self._create_meter_card(apt_name, m))
        self.cards_layout.addStretch()
        self._update_counter()

    def _create_meter_card(self, apt_name: str, meter: Dict) -> QWidget:
        card = QFrame()
        card.setObjectName("GlassCard")
        layout = QVBoxLayout(card)

        wtype_str = "ХВС" if meter['type'] == 'cold' else "ГВС"
        key = (apt_name, meter['type'], meter['num'])
        prev_val = f"{meter['prev']:.2f}" if meter.get('prev') is not None else "—"

        title = QLabel(f"<b>{wtype_str} №{meter['num']}</b> (Предыдущее показание: <span style='color:#00F2FE;'>{prev_val}</span>)")
        layout.addWidget(title)

        grid = QGridLayout()
        edit_old = QLineEdit()
        edit_old.setStyleSheet("background-color: #0F172A; color: #F8FAFC; border: 1px solid #64748B;")
        
        edit_new = QLineEdit()
        edit_new.setStyleSheet("background-color: rgba(16, 185, 129, 0.15); color: #10B981; border: 1.5px solid #10B981;")

        grid.addWidget(QLabel("<b>Финальное старому:</b>"), 0, 0)
        grid.addWidget(edit_old, 0, 1)
        grid.addWidget(QLabel("<b>Начальное новому:</b>"), 1, 0)
        grid.addWidget(edit_new, 1, 1)
        layout.addLayout(grid)

        if key in self.closed_records and key in self.new_records:
            edit_old.setText(str(self.closed_records[key].final_reading))
            edit_new.setText(str(self.new_records[key].initial_reading))

        btn_box = QHBoxLayout()
        btn_apply = QPushButton("✓ Сохранить замену", objectName="AccentButton")
        btn_reset = QPushButton("Сбросить", objectName="SecondaryButton")

        def save():
            try:
                f_val = float(edit_old.text().replace(',', '.'))
                i_val = float(edit_new.text().replace(',', '.'))
                self.closed_records[key] = ClosedMeterRecord(apt_name, meter['type'], meter['num'], f_val)
                self.new_records[key] = NewMeterRecord(apt_name, meter['type'], meter['num'], i_val)
                ToastNotification.show_toast(self.window(), "Замена сохранена!", "SUCCESS")
                self._update_counter()
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Введите числовые значения показаний!")

        def reset():
            self.closed_records.pop(key, None)
            self.new_records.pop(key, None)
            edit_old.clear()
            edit_new.clear()
            self._update_counter()

        btn_apply.clicked.connect(save)
        btn_reset.clicked.connect(reset)
        btn_box.addWidget(btn_apply)
        btn_box.addWidget(btn_reset)
        layout.addLayout(btn_box)

        return card

    def _update_counter(self):
        self.lbl_info.setText(f"Оформлено замен: {len(self.closed_records)}")

    def get_results(self) -> Tuple[List[ClosedMeterRecord], List[NewMeterRecord]]:
        return list(self.closed_records.values()), list(self.new_records.values())
''',

    "ui/main_window.py": '''# ui/main_window.py
import os
import sys
import traceback
from typing import List

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel,
    QPushButton, QStackedWidget, QStatusBar, QProgressBar, QDialog
)
from PySide6.QtCore import QThread, Signal, QPropertyAnimation, QEasingCurve

from core.calculator import WaterCalculator
from core.excel_parser import ExcelManager
from models import CalculationConfig, ClosedMeterRecord, NewMeterRecord

from ui.styles import DARK_AZURE_QSS
from ui.dashboard_page import MainDashboardPage
from ui.norms_page import NormsPage
from ui.logs_page import LogsPage
from ui.test_tab import AutoTestsPage
from ui.about_page import AboutPage
from ui.components.interactive import ToastNotification
from ui.dialogs.replacement_dialog import MeterReplacementDialog

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
            self.log_signal.emit(f"Ошибка: {e}\\n{traceback.format_exc()}", "ERROR")
            self.finished_signal.emit(False, str(e))


class CollapsibleSidebar(QFrame):
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

        self.lbl_brand = QLabel("🌊 WaterMetrics")
        self.lbl_brand.setStyleSheet("font-size: 16px; font-weight: bold; color: #00F2FE;")

        self.btn_toggle = QPushButton("☰", objectName="SecondaryButton")
        self.btn_toggle.setFixedSize(36, 36)
        self.btn_toggle.clicked.connect(self.toggle_sidebar)

        header.addWidget(self.lbl_brand)
        header.addStretch()
        header.addWidget(self.btn_toggle)
        layout.addLayout(header)

        self.nav_items_data = [
            ("🛠  Дашборд", "🛠", 0),
            ("📐  Нормативы", "📐", 1),
            ("📋  Терминал логов", "📋", 2),
            ("🧪  Авто-тесты", "🧪", 3),
            ("ℹ️  О программе", "ℹ️", 4)
        ]

        self.nav_buttons = []
        for full_text, short_text, page_idx in self.nav_items_data:
            btn = QPushButton(full_text)
            btn.setProperty("class", "navBtn")
            btn.setCheckable(True)
            btn.setProperty("fullText", full_text)
            btn.setProperty("shortText", short_text)
            btn.setProperty("pageIndex", page_idx)
            btn.setFixedHeight(42)

            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addStretch()

    def toggle_sidebar(self):
        start_w = self.width()
        end_w = self.collapsed_w if not self.is_collapsed else self.expanded_w

        self.anim = QPropertyAnimation(self, b"minimumWidth")
        self.anim.setDuration(220)
        self.anim.setStartValue(start_w)
        self.anim.setEndValue(end_w)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        self.anim_max = QPropertyAnimation(self, b"maximumWidth")
        self.anim_max.setDuration(220)
        self.anim_max.setStartValue(start_w)
        self.anim_max.setEndValue(end_w)
        self.anim_max.setEasingCurve(QEasingCurve.OutCubic)

        self.anim.start()
        self.anim_max.start()

        self.is_collapsed = not self.is_collapsed
        self.lbl_brand.setVisible(not self.is_collapsed)

        for btn in self.nav_buttons:
            if self.is_collapsed:
                btn.setText(btn.property("shortText"))
                btn.setToolTip(btn.property("fullText"))
            else:
                btn.setText(btn.property("fullText"))
                btn.setToolTip("")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WaterMetrics — Dark Tech Azure Glassmorphism")
        self.resize(1120, 740)

        self.excel_manager = ExcelManager()
        self.closed_meters: List[ClosedMeterRecord] = []
        self.new_meters: List[NewMeterRecord] = []

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("MainContainer")
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = CollapsibleSidebar()
        main_layout.addWidget(self.sidebar)

        # Надежный стандартный QStackedWidget без конфликтующих эффектов прозрачности
        self.stack = QStackedWidget()
        self.page_main = MainDashboardPage(self)
        self.page_norms = NormsPage(self)
        self.page_logs = LogsPage(self)
        self.page_tests = AutoTestsPage(self)
        self.page_about = AboutPage(self)

        self.stack.addWidget(self.page_main)
        self.stack.addWidget(self.page_norms)
        self.stack.addWidget(self.page_logs)
        self.stack.addWidget(self.page_tests)
        self.stack.addWidget(self.page_about)

        main_layout.addWidget(self.stack, 1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Система готова к работе")
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(180)
        self.progress_bar.setVisible(False)

        self.status_bar.addWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.progress_bar)

        for btn in self.sidebar.nav_buttons:
            btn.clicked.connect(self._on_nav_clicked)

        self.switch_page(0)

    def _on_nav_clicked(self):
        sender = self.sender()
        if sender:
            idx = sender.property("pageIndex")
            self.switch_page(idx)

    def switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.sidebar.nav_buttons):
            btn.setChecked(i == index)

    def open_replacement_dialog(self):
        tpl_path = self.page_main.drop_tpl.file_path
        if not tpl_path or not os.path.exists(tpl_path):
            ToastNotification.show_toast(self, "Сначала перетащите файл шаблона!", "ERROR")
            return

        apts_data = self.excel_manager.extract_apartments_and_meters(tpl_path)
        dlg = MeterReplacementDialog(self, apts_data, self.closed_meters, self.new_meters)
        if dlg.exec() == QDialog.Accepted:
            self.closed_meters, self.new_meters = dlg.get_results()
            ToastNotification.show_toast(self, f"Зафиксировано замен: {len(self.closed_meters)}", "SUCCESS")

    def run_calculation(self):
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

        self.calc_worker = CalculationWorker(config, self.excel_manager)
        self.calc_worker.file_created_signal.connect(self.page_main.add_history_entry)
        self.calc_worker.finished_signal.connect(self.calculation_finished)
        self.calc_worker.start()

    def calculation_finished(self, success: bool, message: str):
        self.page_main.btn_run.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Готов к работе")

        if success:
            self.page_main.water_gauge.set_level(1.0)
            ToastNotification.show_toast(self, "Файл успешно сформирован!", "SUCCESS")
        else:
            self.page_main.water_gauge.set_level(0.0)
            ToastNotification.show_toast(self, f"Ошибка: {message}", "ERROR")
''',

    "main.py": '''# main.py
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.styles import DARK_AZURE_QSS

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_AZURE_QSS)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
'''
}

def generate_structure():
    print("🚀 Перезапись файлов UI (Устранение графических конфликтов и багов верстки)...")
    for path, code in FILES.items():
        dir_name = os.path.dirname(path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"📄 Записан исправленный файл: {path}")

    print("\n✅ Исправление завершено! Запустите программу командой: python main.py")

if __name__ == "__main__":
    generate_structure()