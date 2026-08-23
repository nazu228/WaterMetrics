"""
Apple Frosted Glass Toast Notification для WaterMetrics.
Капсульные матовые плавающие уведомления в стиле iOS Control Center.
Сквозные для кликов мыши (WA_TransparentForMouseEvents) с анимацией всплытия (250 мс).
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QFrame, QLabel
from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont

from ui.styles import ThemeManager


class ToastNotification(QWidget):
    """Премиальное матовое уведомление в стиле Apple iOS."""

    def __init__(self, parent: QWidget, message: str, level: str = "INFO"):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.SubWindow | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Сквозной проход кликов мыши (не блокирует подлежащие кнопки)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setObjectName("toastContainer")

        theme_accent = ThemeManager.get_current_accent_color()
        color_map = {
            "INFO": (theme_accent, "ℹ️"),
            "SUCCESS": ("#10B981", "✅"),
            "ERROR": ("#EF4444", "❌")
        }
        accent_color, icon_symbol = color_map.get(level.upper(), (theme_accent, "ℹ️"))

        # Apple Frosted Glass стилизация плашки с верхним бликом Specular Edge
        container.setStyleSheet(f"""
            QFrame#toastContainer {{
                background-color: rgba(18, 24, 38, 0.82);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-top: 1px solid rgba(255, 255, 255, 0.35);
                border-radius: 18px;
            }}
        """)

        c_layout = QHBoxLayout(container)
        c_layout.setContentsMargins(12, 8, 16, 8)
        c_layout.setSpacing(10)

        # Круглый неоновый индикатор уровня (Squircle Badge)
        badge = QLabel()
        badge.setFixedSize(26, 26)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-top: 1px solid rgba(255, 255, 255, 0.35);
                border-radius: 13px;
                color: {accent_color};
                font-size: 11px;
            }}
        """)
        badge.setText(icon_symbol)

        lbl = QLabel(message)
        lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #F8FAFC; background: transparent;")

        c_layout.addWidget(badge)
        c_layout.addWidget(lbl)

        layout.addWidget(container)
        self.adjustSize()

        if parent:
            p_rect = parent.rect()
            margin = 20
            start_x = p_rect.width() - self.width() - margin
            start_y = p_rect.height() + 10
            end_y = p_rect.height() - self.height() - margin

            self.move(start_x, start_y)

            # Плавная быстрая анимация появление (250 мс)
            self.anim = QPropertyAnimation(self, b"pos")
            self.anim.setDuration(250)
            self.anim.setStartValue(QPoint(start_x, start_y))
            self.anim.setEndValue(QPoint(start_x, end_y))
            self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.anim.start()

        QTimer.singleShot(3000, self.fadeOut)

    def fadeOut(self):
        if self.parent():
            p_rect = self.parent().rect()
            end_y = p_rect.height() + 10

            self.anim_out = QPropertyAnimation(self, b"pos")
            self.anim_out.setDuration(200)
            self.anim_out.setStartValue(self.pos())
            self.anim_out.setEndValue(QPoint(self.x(), end_y))
            self.anim_out.setEasingCurve(QEasingCurve.Type.InCubic)
            self.anim_out.finished.connect(self.close)
            self.anim_out.start()

    @staticmethod
    def show_toast(parent: QWidget, message: str, level: str = "INFO"):
        if parent:
            toast = ToastNotification(parent, message, level)
            toast.show()