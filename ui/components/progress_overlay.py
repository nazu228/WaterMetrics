"""
Пошаговый анимированный оверлей прогресса расчета (CalculationProgressOverlay).
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar
from PySide6.QtCore import Qt, QSize
from ui.styles import ThemeManager, get_svg_icon


class CalculationProgressOverlay(QWidget):
    """Пошаговый оверлей прогресса выполнения расчета."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVisible(False)
        self.step_labels = []
        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Подложка полупрозрачного стекла
        self.bg_frame = QFrame(self)

        self.card = QFrame()
        self.card.setObjectName("GlassCard")
        self.card.setFixedSize(460, 240)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(14)

        self.lbl_main_title = QLabel("⚡ Выполнение расчета WaterMetrics", objectName="PageTitle")
        card_layout.addWidget(self.lbl_main_title)

        self.steps_data = [
            ("1. Чтение и проверка входных данных Excel", "folder"),
            ("2. Расчет 3 законов водопотребления", "norms"),
            ("3. Сохранение финального отчета", "save")
        ]

        self.step_labels = []
        for text, icon_key in self.steps_data:
            row = QHBoxLayout()
            lbl_icon = QLabel()
            lbl_txt = QLabel(text)

            row.addWidget(lbl_icon)
            row.addWidget(lbl_txt, 1)
            card_layout.addLayout(row)
            self.step_labels.append((lbl_icon, lbl_txt, icon_key))

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(6)
        card_layout.addWidget(self.progress_bar)

        root_layout.addWidget(self.card)
        self._apply_theme()

    def _apply_theme(self):
        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        accent = ThemeManager.get_current_accent_color()

        if curr_theme == "Как дома":
            card_bg = "#ECE9D8"
            card_border = "#7F9DB9"
            card_radius = "4px"
            title_col = "#0A246A"
            bg_overlay = "rgba(100, 100, 100, 0.4)"
        elif curr_theme == "Pearl Light":
            card_bg = "rgba(248, 250, 252, 0.98)"
            card_border = "#028090"
            card_radius = "18px"
            title_col = "#028090"
            bg_overlay = "rgba(15, 23, 42, 0.35)"
        else:
            card_bg = "rgba(15, 23, 42, 0.95)"
            card_border = accent
            card_radius = "18px"
            title_col = accent
            bg_overlay = "rgba(2, 6, 23, 0.7)"

        if hasattr(self, 'bg_frame'):
            self.bg_frame.setStyleSheet(f"background-color: {bg_overlay};")

        if hasattr(self, 'card'):
            self.card.setStyleSheet(f"""
                QFrame#GlassCard {{
                    background-color: {card_bg};
                    border: 1.5px solid {card_border};
                    border-radius: {card_radius};
                }}
            """)

        if hasattr(self, 'lbl_main_title'):
            self.lbl_main_title.setStyleSheet(f"color: {title_col}; font-size: 16px; font-weight: 700;")

    def set_step(self, step_idx: int):
        """Установка текущего активного шага (0, 1, 2)."""
        self._apply_theme()
        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        accent = ThemeManager.get_current_accent_color()

        active_col = ("#0A246A" if curr_theme == "Как дома" else "#028090") if is_light else accent
        done_col = "#15803D" if is_light else "#10B981"
        pending_col = "#64748B" if is_light else "#94A3B8"

        for idx, (lbl_icon, lbl_txt, icon_key) in enumerate(self.step_labels):
            if idx < step_idx:
                lbl_icon.setPixmap(get_svg_icon("tests", color=done_col).pixmap(20, 20))
                lbl_txt.setStyleSheet(f"color: {done_col}; font-size: 13px; font-weight: 700;")
            elif idx == step_idx:
                lbl_icon.setPixmap(get_svg_icon(icon_key, color=active_col).pixmap(20, 20))
                lbl_txt.setStyleSheet(f"color: {active_col}; font-size: 13px; font-weight: 700;")
            else:
                lbl_icon.setPixmap(get_svg_icon(icon_key, color=pending_col).pixmap(20, 20))
                lbl_txt.setStyleSheet(f"color: {pending_col}; font-size: 13px; font-weight: 500;")

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_theme()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.parentWidget():
            self.setGeometry(0, 0, self.parentWidget().width(), self.parentWidget().height())
            if hasattr(self, 'bg_frame'):
                self.bg_frame.setGeometry(0, 0, self.width(), self.height())
