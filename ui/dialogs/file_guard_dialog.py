"""
ui/dialogs/file_guard_dialog.py — Премиальные диалоги защиты от ошибок при выборе и сохранении файлов (WaterMetrics).
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QWidget
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush, QLinearGradient

from ui.styles import ThemeManager, get_svg_icon
from ui.components.glass_icon import GlassIconWidget


class FileGuardDialog(QDialog):
    """Стильное матовое окно защиты данных (File Guard Shield)."""

    def __init__(self, parent=None, title="Защита файлов", message="", icon_name="warning", buttons=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Dialog
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(560, 260)
        self.title_str = title
        self.message_str = message
        self.icon_name = icon_name
        self.buttons_config = buttons or []
        self.selected_action = None

        self.init_ui()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        theme_name = ThemeManager.get_current_theme_name()
        accent = ThemeManager.get_current_accent_color()
        is_light = theme_name in ("Pearl Light", "Как дома")

        path = QPainterPath()
        path.addRoundedRect(rect, 14, 14)

        if is_light:
            grad = QLinearGradient(0, 0, 0, rect.height())
            grad.setColorAt(0.0, QColor(255, 255, 255, 255))
            grad.setColorAt(1.0, QColor(241, 245, 249, 252))
            border_pen = QPen(QColor(accent), 1.8)
        else:
            grad = QLinearGradient(0, 0, 0, rect.height())
            grad.setColorAt(0.0, QColor(18, 28, 50, 252))
            grad.setColorAt(1.0, QColor(15, 23, 42, 252))
            border_pen = QPen(QColor(accent), 1.8)

        painter.setPen(border_pen)
        painter.setBrush(QBrush(grad))
        painter.drawPath(path)

    def init_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(24, 20, 24, 20)
        root_lay.setSpacing(14)

        theme_name = ThemeManager.get_current_theme_name()
        accent = ThemeManager.get_current_accent_color()
        is_light = theme_name in ("Pearl Light", "Как дома")

        # ─── Шапка ───
        hdr = QHBoxLayout()
        hdr.setSpacing(12)

        icon_col = "#F59E0B" if self.icon_name in ("warning", "alert") else accent
        self.icon_widget = GlassIconWidget("help_wizard", color=icon_col, size=QSize(38, 38))
        hdr.addWidget(self.icon_widget)

        self.lbl_title = QLabel(self.title_str)
        title_col = "#0A246A" if theme_name == "Как дома" else ("#0F172A" if is_light else "#F8FAFC")
        self.lbl_title.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {title_col}; background: transparent;")
        hdr.addWidget(self.lbl_title, 1)

        btn_x = QPushButton("✕")
        btn_x.setFixedSize(30, 30)
        btn_x.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn_bg = "rgba(0, 0, 0, 0.06)" if is_light else "rgba(255, 255, 255, 0.06)"
        close_btn_col = "#334155" if is_light else "#94A3B8"
        close_btn_border = "rgba(0, 0, 0, 0.15)" if is_light else "rgba(255, 255, 255, 0.12)"
        btn_x.setStyleSheet(f"""
            QPushButton {{
                background: {close_btn_bg};
                color: {close_btn_col};
                border: 1px solid {close_btn_border};
                border-radius: 15px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.25);
                color: #EF4444;
            }}
        """)
        btn_x.clicked.connect(self.reject)
        hdr.addWidget(btn_x)

        root_lay.addLayout(hdr)

        # ─── Текст сообщения ───
        msg_frame = QFrame()
        msg_frame.setStyleSheet(f"""
            background: {'rgba(0, 0, 0, 0.03)' if is_light else 'rgba(255, 255, 255, 0.03)'};
            border: 1.5px solid {'rgba(0, 0, 0, 0.08)' if is_light else 'rgba(255, 255, 255, 0.08)'};
            border-radius: 10px;
            padding: 14px;
        """)
        msg_lay = QVBoxLayout(msg_frame)
        msg_lay.setContentsMargins(12, 10, 12, 10)

        self.lbl_msg = QLabel(self.message_str)
        self.lbl_msg.setWordWrap(True)
        self.lbl_msg.setStyleSheet(f"color: {'#334155' if is_light else '#E2E8F0'}; font-size: 13.5px; line-height: 1.45; background: transparent;")
        msg_lay.addWidget(self.lbl_msg)
        root_lay.addWidget(msg_frame, 1)

        # ─── Кнопки действий ───
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        for btn_text, action_key, obj_name in self.buttons_config:
            b = QPushButton(btn_text, objectName=obj_name)
            b.setMinimumHeight(36)
            b.setStyleSheet("font-size: 13px; font-weight: 700;")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda chk=False, act=action_key: self._on_btn_clicked(act))
            btn_box.addWidget(b)

        root_lay.addLayout(btn_box)

    def _on_btn_clicked(self, action_key: str):
        self.selected_action = action_key
        self.accept()

    @classmethod
    def show_excel_locked_dialog(cls, parent, filename: str, safe_copy_filename: str) -> str:
        """
        Диалог при блокировке файла Excel.
        Возвращает: 'copy', 'retry', 'cancel'
        """
        msg = (
            f"Файл <b>«{filename}»</b> в данный момент открыт в Microsoft Excel или другой программе.<br/><br/>"
            f"• Вы можете нажать <b>«Сохранить как копию»</b> для мгновенной записи в <b>{safe_copy_filename}</b><br/>"
            f"• Либо закройте файл в Excel и нажмите <b>«Повторить попытку»</b>."
        )
        buttons = [
            (f"📄 Сохранить как копию ({safe_copy_filename})", "copy", "PrimaryButton"),
            ("🔄 Повторить", "retry", "SecondaryButton"),
            ("Отмена", "cancel", "SecondaryButton")
        ]
        dlg = cls(parent, title="⚠️ Файл заблокирован в Excel", message=msg, icon_name="warning", buttons=buttons)
        dlg.exec()
        return dlg.selected_action or "cancel"

    @classmethod
    def show_house_mismatch_dialog(cls, parent, tpl_house: str, arc_house: str, match_pct: float = 0.0) -> bool:
        """
        Диалог при несовпадении дома шаблона и файла Аркус.
        Возвращает: True (продолжить расчет), False (отмена)
        """
        msg = (
            f"<b>Обнаружено несовпадение объектов!</b><br/><br/>"
            f"• Шаблон: <b>«{tpl_house}»</b><br/>"
            f"• Файл Аркус: <b>«{arc_house}»</b><br/>"
            f"• Совпадение квартир: <b>{match_pct:.1f}%</b><br/><br/>"
            f"<span style='color: #F87171;'>При продолжении расчета лицевые счета могут не сойтись и всем квартирам будут начислены нормативы.</span>"
        )
        buttons = [
            ("Отмена (Проверить файлы)", "cancel", "PrimaryButton"),
            ("⚠️ Всё равно продолжить", "continue", "DangerButton")
        ]
        dlg = cls(parent, title="🛑 Внимание: Несовпадение домов!", message=msg, icon_name="alert", buttons=buttons)
        dlg.exec()
        return dlg.selected_action == "continue"

    @classmethod
    def show_month_mismatch_dialog(cls, parent, tpl_house: str, target_month_str: str, arc_month_str: str, arc_path: str) -> bool:
        """
        Диалог при несовпадении папки месяца файла Аркус с целевым расчетным месяцем.
        Возвращает: True (продолжить расчет), False (отмена)
        """
        msg = (
            f"<b>Файл Аркуса выбран не из папки следующего месяца!</b><br/><br/>"
            f"• Объект: <b>«{tpl_house}»</b><br/>"
            f"• Целевой расчетный месяц: <b style='color: #10B981;'>{target_month_str}</b><br/>"
            f"• Папка выбранного Аркуса: <b style='color: #F87171;'>{arc_month_str}</b><br/>"
            f"• Путь: <span style='font-size: 10px; color: #94A3B8;'>{arc_path}</span><br/><br/>"
            f"<span style='color: #F87171;'>Внимание: Файл Аркус должен браться строго из папки следующего месяца ({target_month_str}), иначе показания будут рассчитаны за некорректный период!</span>"
        )
        buttons = [
            ("Выбрать другой файл", "cancel", "PrimaryButton"),
            ("⚠️ Всё равно продолжить", "continue", "DangerButton")
        ]
        dlg = cls(parent, title="⚠️ Несовпадение месяца Аркуса!", message=msg, icon_name="warning", buttons=buttons)
        dlg.exec()
        return dlg.selected_action == "continue"

    @classmethod
    def show_overwrite_warning_dialog(cls, parent, filename: str, info_str: str) -> str:
        """
        Диалог при наличии уже сформированного отчета.
        Возвращает: 'overwrite', 'copy', 'cancel'
        """
        msg = (
            f"В целевой папке уже найден ранее сформированный отчет:<br/>"
            f"<b>{info_str}</b><br/><br/>"
            f"Вы хотите перезаписать его новым расчетом или сохранить как отдельную версию?"
        )
        buttons = [
            ("Перезаписать отчет", "overwrite", "PrimaryButton"),
            ("Сохранить как копию", "copy", "SecondaryButton"),
            ("Отмена", "cancel", "SecondaryButton")
        ]
        dlg = cls(parent, title="ℹ️ Отчет уже существует", message=msg, icon_name="warning", buttons=buttons)
        dlg.exec()
        return dlg.selected_action or "cancel"
