"""
ui/about_page.py — Экран "О программе", Кастомизация 3D-волн, Минимализм и Обратная связь.
"""

import os
import sys
import urllib.parse
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QDialog, QFrame, QApplication, QSlider, QCheckBox, QScrollArea, QLineEdit
)
from PySide6.QtCore import Qt, QSize, QSettings, Slot, QUrl
from PySide6.QtGui import QMovie, QDesktopServices

from config import APP_VERSION, DEFAULT_GITHUB_REPO
from services.updater_service import GitHubUpdateChecker, GitHubReleaseInfo, VersionManager
from ui.dialogs.update_dialog import UpdateDialog
from ui.dialogs.welcome_dialog import WelcomeSetupDialog
from ui.styles import get_svg_icon, ThemeManager
from ui.components.interactive import HoverGlassCard
from ui.components.toast import ToastNotification
from ui.components.glass_icon import GlassIconWidget


FEEDBACK_EMAIL = "nazuha2281337@gmail.com"
FEEDBACK_SUBJECT_TEMPLATE = f"[WaterMetrics v{APP_VERSION}] Обратная связь / Предложение"
FEEDBACK_BODY_TEMPLATE = f"""Здравствуйте, разработчик WaterMetrics!

• Версия программы: WaterMetrics v{APP_VERSION}
• Операционная система: Windows
• Тема обращения: [Отзыв / Найдена ошибка / Пожелание по улучшению]

Описание ситуации:
[Пожалуйста, опишите ваш вопрос или предложение]
"""


def get_asset_path(filename: str) -> str:
    """
    Универсальный поиск файлов ресурсов (assets).
    """
    candidates = []

    if hasattr(sys, '_MEIPASS'):
        candidates.append(os.path.join(sys._MEIPASS, "assets", filename))
        candidates.append(os.path.join(sys._MEIPASS, filename))

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(os.path.join(base_dir, "assets", filename))
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", filename))

    cwd = os.getcwd()
    candidates.append(os.path.join(cwd, "assets", filename))
    candidates.append(os.path.join(cwd, "pyside", "assets", filename))
    candidates.append(os.path.join(cwd, "pyside", filename))

    for path in candidates:
        norm_p = os.path.normpath(path)
        if os.path.isfile(norm_p):
            return norm_p

    return os.path.normpath(os.path.join(base_dir, "assets", filename))


class DonateDialog(QDialog):
    """Стильное бесшовное модальное окно пожертвований с адаптивной темой."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(480, 270)
        self.card_number = "40817810807004134433"
        self.init_ui()

    def init_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)

        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        accent = ThemeManager.get_current_accent_color()

        self.card = HoverGlassCard()
        if is_light:
            card_bg = "#FFFFFF"
            card_border = "#0A246A" if curr_theme == "Как дома" else "#028090"
            self.card.setStyleSheet(f"QFrame#GlassCard {{ background-color: {card_bg}; border: 1.5px solid {card_border}; border-radius: 18px; }} QFrame#GlassCard:hover, QFrame#GlassCard[hover=\"true\"] {{ background-color: {card_bg}; border: 1.5px solid {card_border}; }}")
        else:
            self.card.setStyleSheet(f"QFrame#GlassCard {{ background-color: #0B1736; border: 1.5px solid {accent}; border-radius: 18px; }} QFrame#GlassCard:hover, QFrame#GlassCard[hover=\"true\"] {{ background-color: #0F2048; border: 1.5px solid {accent}; }}")

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        lbl_title = QLabel("Поддержка разработки WaterMetrics", objectName="PageTitle")
        title_col = "#0A246A" if curr_theme == "Как дома" else ("#0F172A" if curr_theme == "Pearl Light" else "#F8FAFC")
        lbl_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {title_col};")
        
        btn_x = QPushButton("✕")
        btn_x.setFixedSize(28, 28)
        btn_x.setCursor(Qt.PointingHandCursor)
        close_btn_bg = "rgba(0, 0, 0, 0.06)" if is_light else "rgba(255, 255, 255, 0.08)"
        close_btn_col = "#334155" if is_light else "#94A3B8"
        close_btn_border = "rgba(0, 0, 0, 0.15)" if is_light else "rgba(255, 255, 255, 0.15)"
        btn_x.setStyleSheet(f"""
            QPushButton {{
                background: {close_btn_bg};
                color: {close_btn_col};
                border: 1px solid {close_btn_border};
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.55);
                color: #FFFFFF;
                border-color: #EF4444;
            }}
        """)
        btn_x.clicked.connect(self.reject)

        header_row.addWidget(lbl_title, 1)
        header_row.addWidget(btn_x)
        layout.addLayout(header_row)

        card_frame = HoverGlassCard()
        if is_light:
            inner_bg = "rgba(10, 36, 106, 0.04)" if curr_theme == "Как дома" else "rgba(2, 128, 144, 0.05)"
            inner_border = "#7F9DB9" if curr_theme == "Как дома" else "rgba(2, 128, 144, 0.25)"
            card_frame.setStyleSheet(f"QFrame#GlassCard {{ background-color: {inner_bg}; border: 1px solid {inner_border}; border-radius: 12px; }} QFrame#GlassCard:hover, QFrame#GlassCard[hover=\"true\"] {{ background-color: {inner_bg}; border: 1px solid {inner_border}; }}")
        else:
            card_frame.setStyleSheet(f"QFrame#GlassCard {{ background-color: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.10); border-radius: 12px; }}")

        card_lay = QVBoxLayout(card_frame)
        card_lay.setContentsMargins(16, 12, 16, 12)
        card_lay.setSpacing(6)

        lbl_bank = QLabel("Сбербанк / Номер счета / карты:")
        sub_col = "#475569" if is_light else "#94A3B8"
        lbl_bank.setStyleSheet(f"color: {sub_col}; font-size: 12px; font-weight: 500;")

        lbl_num = QLabel(self.card_number)
        num_col = ("#0A246A" if curr_theme == "Как дома" else "#028090") if is_light else accent
        lbl_num.setStyleSheet(f"""
            color: {num_col};
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 17px;
            font-weight: bold;
            letter-spacing: 1.5px;
            background: transparent;
        """)
        lbl_num.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        card_lay.addWidget(lbl_bank)
        card_lay.addWidget(lbl_num)
        layout.addWidget(card_frame)

        btn_box = QHBoxLayout()
        btn_copy = QPushButton("  Скопировать номер", objectName="PrimaryButton")
        copy_icon_col = "#FFFFFF" if is_light else "#020617"
        btn_copy.setIcon(get_svg_icon("copy", color=copy_icon_col))
        btn_copy.setMinimumHeight(36)
        btn_copy.clicked.connect(self._copy_to_clipboard)

        btn_close = QPushButton("Закрыть", objectName="SecondaryButton")
        btn_close.setMinimumHeight(36)
        btn_close.clicked.connect(self.accept)

        btn_box.addWidget(btn_copy, 1)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

        root_lay.addWidget(self.card)

    def _copy_to_clipboard(self):
        QApplication.clipboard().setText(self.card_number)
        ToastNotification.show_toast(self, "Номер карты скопирован в буфер обмена!", "SUCCESS")


class BeachRestDialog(QDialog):
    """Бесшовный модальный диалог морского отдыха."""

    def __init__(self, gif_path: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(540, 440)
        self.gif_path = gif_path
        self.init_ui()

    def init_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)

        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")

        self.card = HoverGlassCard()
        if is_light:
            card_bg = "#FFFFFF"
            card_border = "#0A246A" if curr_theme == "Как дома" else "#028090"
            self.card.setStyleSheet(f"QFrame#GlassCard {{ background-color: {card_bg}; border: 1.5px solid {card_border}; border-radius: 18px; }} QFrame#GlassCard:hover, QFrame#GlassCard[hover=\"true\"] {{ background-color: {card_bg}; border: 1.5px solid {card_border}; }}")
        else:
            accent = ThemeManager.get_current_accent_color()
            self.card.setStyleSheet(f"QFrame#GlassCard {{ background-color: #0B1736; border: 1.5px solid {accent}; border-radius: 18px; }} QFrame#GlassCard:hover, QFrame#GlassCard[hover=\"true\"] {{ background-color: #0F2048; border: 1.5px solid {accent}; }}")

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        lbl_title = QLabel("Приятного отдыха!", objectName="PageTitle")
        title_col = "#0A246A" if curr_theme == "Как дома" else ("#0F172A" if curr_theme == "Pearl Light" else "#F8FAFC")
        lbl_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {title_col};")
        
        btn_x = QPushButton("✕")
        btn_x.setFixedSize(28, 28)
        btn_x.setCursor(Qt.PointingHandCursor)
        close_btn_bg = "rgba(0, 0, 0, 0.06)" if is_light else "rgba(255, 255, 255, 0.08)"
        close_btn_col = "#334155" if is_light else "#94A3B8"
        close_btn_border = "rgba(0, 0, 0, 0.15)" if is_light else "rgba(255, 255, 255, 0.15)"
        btn_x.setStyleSheet(f"""
            QPushButton {{
                background: {close_btn_bg};
                color: {close_btn_col};
                border: 1px solid {close_btn_border};
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.55);
                color: #FFFFFF;
                border-color: #EF4444;
            }}
        """)
        btn_x.clicked.connect(self.accept)

        header_row.addWidget(lbl_title, 1)
        header_row.addWidget(btn_x)
        layout.addLayout(header_row)

        card_inner = HoverGlassCard()
        if is_light:
            inner_bg = "rgba(10, 36, 106, 0.04)" if curr_theme == "Как дома" else "rgba(2, 128, 144, 0.05)"
            inner_border = "#7F9DB9" if curr_theme == "Как дома" else "rgba(2, 128, 144, 0.25)"
            card_inner.setStyleSheet(f"QFrame#GlassCard {{ background-color: {inner_bg}; border: 1px solid {inner_border}; border-radius: 12px; }} QFrame#GlassCard:hover, QFrame#GlassCard[hover=\"true\"] {{ background-color: {inner_bg}; border: 1px solid {inner_border}; }}")
        else:
            card_inner.setStyleSheet(f"QFrame#GlassCard {{ background-color: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.10); border-radius: 12px; }}")

        card_lay = QVBoxLayout(card_inner)
        card_lay.setContentsMargins(8, 8, 8, 8)

        self.lbl_gif = QLabel()
        self.lbl_gif.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_gif.setStyleSheet("background: transparent;")

        if os.path.exists(self.gif_path):
            self.movie = QMovie(self.gif_path)
            self.lbl_gif.setMovie(self.movie)
            self.movie.start()
        else:
            self.lbl_gif.setText("Файл анимации пляжа не найден")
            self.lbl_gif.setStyleSheet("color: #F87171; font-size: 13px;")

        card_lay.addWidget(self.lbl_gif)
        layout.addWidget(card_inner, 1)

        btn_close = QPushButton("Вернуться к работе", objectName="PrimaryButton")
        btn_close.setMinimumHeight(36)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        root_lay.addWidget(self.card)

    def closeEvent(self, event):
        if hasattr(self, 'movie') and self.movie:
            self.movie.stop()
        super().closeEvent(event)


class FeedbackDialog(QDialog):
    """Интерактивное окно обратной связи и отправки писем разработчику."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(540, 380)
        self.init_ui()

    def init_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(0, 0, 0, 0)

        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        accent = ThemeManager.get_current_accent_color()

        self.card = HoverGlassCard()
        if is_light:
            card_bg = "#FFFFFF"
            card_border = "#0A246A" if curr_theme == "Как дома" else "#028090"
            self.card.setStyleSheet(f"QFrame#GlassCard {{ background-color: {card_bg}; border: 1.5px solid {card_border}; border-radius: 18px; }} QFrame#GlassCard:hover, QFrame#GlassCard[hover=\"true\"] {{ background-color: {card_bg}; border: 1.5px solid {card_border}; }}")
        else:
            self.card.setStyleSheet(f"QFrame#GlassCard {{ background-color: #0B1736; border: 1.5px solid {accent}; border-radius: 18px; }} QFrame#GlassCard:hover, QFrame#GlassCard[hover=\"true\"] {{ background-color: #0F2048; border: 1.5px solid {accent}; }}")

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        lbl_title = QLabel("Обратная связь с разработчиком", objectName="PageTitle")
        title_col = "#0A246A" if curr_theme == "Как дома" else ("#0F172A" if curr_theme == "Pearl Light" else "#F8FAFC")
        lbl_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {title_col};")
        
        btn_x = QPushButton("✕")
        btn_x.setFixedSize(28, 28)
        btn_x.setCursor(Qt.PointingHandCursor)
        close_btn_bg = "rgba(0, 0, 0, 0.06)" if is_light else "rgba(255, 255, 255, 0.08)"
        close_btn_col = "#334155" if is_light else "#94A3B8"
        close_btn_border = "rgba(0, 0, 0, 0.15)" if is_light else "rgba(255, 255, 255, 0.15)"
        btn_x.setStyleSheet(f"""
            QPushButton {{
                background: {close_btn_bg};
                color: {close_btn_col};
                border: 1px solid {close_btn_border};
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.55);
                color: #FFFFFF;
                border-color: #EF4444;
            }}
        """)
        btn_x.clicked.connect(self.reject)

        header_row.addWidget(lbl_title, 1)
        header_row.addWidget(btn_x)
        layout.addLayout(header_row)

        info_card = HoverGlassCard()
        if is_light:
            inner_bg = "rgba(10, 36, 106, 0.04)" if curr_theme == "Как дома" else "rgba(2, 128, 144, 0.05)"
            inner_border = "#7F9DB9" if curr_theme == "Как дома" else "rgba(2, 128, 144, 0.25)"
            info_card.setStyleSheet(f"QFrame#GlassCard {{ background-color: {inner_bg}; border: 1px solid {inner_border}; border-radius: 12px; }} QFrame#GlassCard:hover, QFrame#GlassCard[hover=\"true\"] {{ background-color: {inner_bg}; border: 1px solid {inner_border}; }}")
        else:
            info_card.setStyleSheet(f"QFrame#GlassCard {{ background-color: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.10); border-radius: 12px; }}")

        info_lay = QVBoxLayout(info_card)
        info_lay.setContentsMargins(16, 12, 16, 12)
        info_lay.setSpacing(6)

        lbl_to = QLabel("Email для связи и предложений:")
        lbl_to.setStyleSheet(f"color: {'#475569' if is_light else '#94A3B8'}; font-size: 12px;")
        
        lbl_email = QLabel(FEEDBACK_EMAIL)
        email_col = ("#0A246A" if curr_theme == "Как дома" else "#028090") if is_light else accent
        lbl_email.setStyleSheet(f"color: {email_col}; font-size: 15px; font-weight: bold; font-family: monospace;")
        lbl_email.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        lbl_subj = QLabel(f"Тема письма: {FEEDBACK_SUBJECT_TEMPLATE}")
        lbl_subj.setStyleSheet(f"color: {'#334155' if is_light else '#CBD5E1'}; font-size: 12px; font-weight: 500;")

        info_lay.addWidget(lbl_to)
        info_lay.addWidget(lbl_email)
        info_lay.addWidget(lbl_subj)
        layout.addWidget(info_card)

        btn_grid = QGridLayout()
        btn_grid.setSpacing(10)

        btn_mailto = QPushButton("  Почтовый клиент", objectName="PrimaryButton")
        btn_mailto.setIcon(get_svg_icon("mail", color="#FFFFFF" if is_light else "#020617"))
        btn_mailto.setMinimumHeight(38)
        btn_mailto.clicked.connect(self._open_mailto)

        btn_gmail = QPushButton("  Открыть в Gmail", objectName="SecondaryButton")
        btn_gmail.setIcon(get_svg_icon("external_link", color=accent))
        btn_gmail.setMinimumHeight(38)
        btn_gmail.clicked.connect(self._open_gmail)

        btn_mailru = QPushButton("  Открыть в Mail.ru", objectName="SecondaryButton")
        btn_mailru.setIcon(get_svg_icon("external_link", color=accent))
        btn_mailru.setMinimumHeight(38)
        btn_mailru.clicked.connect(self._open_mailru)

        btn_copy = QPushButton("  Скопировать шаблон", objectName="SecondaryButton")
        btn_copy.setIcon(get_svg_icon("copy", color=accent))
        btn_copy.setMinimumHeight(38)
        btn_copy.clicked.connect(self._copy_template)

        btn_grid.addWidget(btn_mailto, 0, 0)
        btn_grid.addWidget(btn_gmail, 0, 1)
        btn_grid.addWidget(btn_mailru, 1, 0)
        btn_grid.addWidget(btn_copy, 1, 1)
        layout.addLayout(btn_grid)

        btn_close = QPushButton("Закрыть", objectName="SecondaryButton")
        btn_close.setMinimumHeight(34)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        root_lay.addWidget(self.card)

    def _open_mailto(self):
        subject_enc = urllib.parse.quote(FEEDBACK_SUBJECT_TEMPLATE)
        body_enc = urllib.parse.quote(FEEDBACK_BODY_TEMPLATE)
        url = f"mailto:{FEEDBACK_EMAIL}?subject={subject_enc}&body={body_enc}"
        QDesktopServices.openUrl(QUrl(url))
        ToastNotification.show_toast(self, "Запущен системный почтовый клиент!", "SUCCESS")

    def _open_gmail(self):
        subject_enc = urllib.parse.quote(FEEDBACK_SUBJECT_TEMPLATE)
        body_enc = urllib.parse.quote(FEEDBACK_BODY_TEMPLATE)
        url = f"https://mail.google.com/mail/?view=cm&fs=1&to={FEEDBACK_EMAIL}&su={subject_enc}&body={body_enc}"
        QDesktopServices.openUrl(QUrl(url))
        ToastNotification.show_toast(self, "Открываем веб-интерфейс Gmail...", "INFO")

    def _open_mailru(self):
        subject_enc = urllib.parse.quote(FEEDBACK_SUBJECT_TEMPLATE)
        body_enc = urllib.parse.quote(FEEDBACK_BODY_TEMPLATE)
        url = f"https://e.mail.ru/compose/?to={FEEDBACK_EMAIL}&subject={subject_enc}&body={body_enc}"
        QDesktopServices.openUrl(QUrl(url))
        ToastNotification.show_toast(self, "Открываем веб-интерфейс Mail.ru...", "INFO")

    def _copy_template(self):
        full_text = f"Кому: {FEEDBACK_EMAIL}\nТема: {FEEDBACK_SUBJECT_TEMPLATE}\n\n{FEEDBACK_BODY_TEMPLATE}"
        QApplication.clipboard().setText(full_text)
        ToastNotification.show_toast(self, "Email, тема и образец письма скопированы в буфер обмена!", "SUCCESS")


class AboutPage(QWidget):
    """Экран сведений о системе, кастомизации 3D-волн, минимализма и обратной связи."""

    def __init__(self, main_win=None):
        super().__init__()
        self.main_win = main_win
        self.setObjectName("AboutPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(14)

        self.main_title = QLabel("О программе, Настройки 3D-волн и Обратная связь", objectName="PageTitle")
        root_layout.addWidget(self.main_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        accent = ThemeManager.get_current_accent_color()

        # ==============================================================================
        # 1. КАРТОЧКА: СВЕДЕНИЯ О СИСТЕМЕ
        # ==============================================================================
        self.info_card = HoverGlassCard()
        info_lay = QVBoxLayout(self.info_card)
        info_lay.setContentsMargins(24, 20, 24, 20)
        info_lay.setSpacing(12)

        self.glass_app_icon = GlassIconWidget("droplet", accent, size=QSize(48, 48))

        app_header_lay = QHBoxLayout()
        app_header_lay.setSpacing(14)
        app_header_lay.addWidget(self.glass_app_icon)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(3)
        self.appName_label = QLabel("WaterMetrics Professional Edition")
        self.appName_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {accent};")
        
        self.appSub_label = QLabel("Система автоматизированного расчета и распределения объемов водопотребления")
        self.appSub_label.setStyleSheet("font-size: 13px; color: #94A3B8;")
        
        title_vbox.addWidget(self.appName_label)
        title_vbox.addWidget(self.appSub_label)

        app_header_lay.addLayout(title_vbox, 1)
        info_lay.addLayout(app_header_lay)

        self.appVer_label = QLabel(f"Версия: v{APP_VERSION} (PySide6 Apple Frosted Glass & 3D Wave Edition)")
        self.appVer_label.setStyleSheet("font-size: 13px; color: #94A3B8; font-weight: 600;")

        btns_row1 = QHBoxLayout()
        btns_row1.setSpacing(10)

        self.btn_check_update = QPushButton("Проверить обновления", objectName="PrimaryButton")
        self.btn_check_update.setIcon(get_svg_icon("update", color="#020617" if not is_light else "#FFFFFF"))
        self.btn_check_update.setMinimumHeight(38)
        self.btn_check_update.setStyleSheet("font-size: 13px; font-weight: 700;")
        self.btn_check_update.clicked.connect(self.check_updates)

        self.btn_welcome_setup = QPushButton("Стиль и язык", objectName="SecondaryButton")
        self.btn_welcome_setup.setIcon(get_svg_icon("edit"))
        self.btn_welcome_setup.setMinimumHeight(38)
        self.btn_welcome_setup.setStyleSheet("font-size: 13px; font-weight: 600;")
        self.btn_welcome_setup.clicked.connect(self.show_welcome_setup)

        self.btn_onboarding = QPushButton("Обучение проводке", objectName="SecondaryButton")
        self.btn_onboarding.setIcon(get_svg_icon("sparkles"))
        self.btn_onboarding.setMinimumHeight(38)
        self.btn_onboarding.setStyleSheet("font-size: 13px; font-weight: 600;")
        self.btn_onboarding.clicked.connect(self.restart_onboarding)

        btns_row1.addWidget(self.btn_check_update)
        btns_row1.addWidget(self.btn_welcome_setup)
        btns_row1.addWidget(self.btn_onboarding)
        btns_row1.addStretch()

        btns_row2 = QHBoxLayout()
        btns_row2.setSpacing(10)

        self.btn_feedback = QPushButton("Обратная связь", objectName="SecondaryButton")
        self.btn_feedback.setIcon(get_svg_icon("mail"))
        self.btn_feedback.setMinimumHeight(38)
        self.btn_feedback.setStyleSheet("font-size: 13px; font-weight: 600;")
        self.btn_feedback.clicked.connect(self.show_feedback_dialog)

        self.btn_donate = QPushButton("Поддержка", objectName="SecondaryButton")
        self.btn_donate.setIcon(get_svg_icon("about"))
        self.btn_donate.setMinimumHeight(38)
        self.btn_donate.setStyleSheet("font-size: 13px; font-weight: 600;")
        self.btn_donate.clicked.connect(self.show_donate)

        self.btn_beach = QPushButton("Морской Отдых", objectName="AccentButton")
        self.btn_beach.setIcon(get_svg_icon("run"))
        self.btn_beach.setMinimumHeight(38)
        self.btn_beach.setStyleSheet("font-size: 13px; font-weight: 800;")
        self.btn_beach.clicked.connect(self.show_beach)

        btns_row2.addWidget(self.btn_feedback)
        btns_row2.addWidget(self.btn_donate)
        btns_row2.addWidget(self.btn_beach)
        btns_row2.addStretch()

        info_lay.addWidget(self.appVer_label)
        info_lay.addLayout(btns_row1)
        info_lay.addLayout(btns_row2)
        layout.addWidget(self.info_card)

        # ==============================================================================
        # 2. КАРТОЧКА: УДАЛЕННЫЕ ОБНОВЛЕНИЯ ПО (GITHUB RELEASES)
        # ==============================================================================
        self.update_card = HoverGlassCard()
        update_lay = QVBoxLayout(self.update_card)
        update_lay.setContentsMargins(24, 20, 24, 20)
        update_lay.setSpacing(14)

        upd_header_lay = QHBoxLayout()
        upd_header_lay.setSpacing(14)
        self.glass_upd_icon = GlassIconWidget("update", accent, size=QSize(42, 42))
        upd_header_lay.addWidget(self.glass_upd_icon)

        upd_title_vbox = QVBoxLayout()
        upd_title_vbox.setSpacing(2)
        self.lbl_upd_head = QLabel("Удаленные обновления ПО (GitHub Releases)", objectName="SectionTitle")
        self.lbl_upd_head.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {accent};")
        
        self.lbl_upd_sub = QLabel("Автоматическая проверка новых релизов, changelog и 1-click установка")
        self.lbl_upd_sub.setStyleSheet("font-size: 12px; color: #94A3B8;")
        
        upd_title_vbox.addWidget(self.lbl_upd_head)
        upd_title_vbox.addWidget(self.lbl_upd_sub)
        upd_header_lay.addLayout(upd_title_vbox, 1)
        update_lay.addLayout(upd_header_lay)

        upd_settings = QSettings("WaterMetrics", "Updates")
        saved_repo = upd_settings.value("GitHubRepo", DEFAULT_GITHUB_REPO, type=str)
        if not saved_repo or saved_repo == "WaterMetrics/WaterMetrics":
            saved_repo = DEFAULT_GITHUB_REPO
            upd_settings.setValue("GitHubRepo", DEFAULT_GITHUB_REPO)
        auto_check = upd_settings.value("AutoCheckUpdates", True, type=bool)

        repo_row = QHBoxLayout()
        repo_row.setSpacing(10)
        self.lbl_repo = QLabel("Репозиторий GitHub:")
        self.lbl_repo.setStyleSheet("font-size: 12px; color: #CBD5E1; font-weight: 600;")
        
        self.txt_repo = QLineEdit(saved_repo)
        self.txt_repo.setPlaceholderText("owner/repository")
        self.txt_repo.setMinimumHeight(34)
        self.txt_repo.textChanged.connect(self._on_repo_text_changed)

        self.btn_card_check = QPushButton("Проверить сейчас", objectName="PrimaryButton")
        self.btn_card_check.setIcon(get_svg_icon("update", color="#020617" if not is_light else "#FFFFFF"))
        self.btn_card_check.setMinimumHeight(34)
        self.btn_card_check.clicked.connect(self.check_updates)

        repo_row.addWidget(self.lbl_repo)
        repo_row.addWidget(self.txt_repo, 1)
        repo_row.addWidget(self.btn_card_check)
        update_lay.addLayout(repo_row)

        self.chk_auto_updates = QCheckBox("Автоматически проверять обновления при каждом запуске")
        self.chk_auto_updates.setChecked(auto_check)
        self.chk_auto_updates.toggled.connect(self._on_auto_check_toggled)
        update_lay.addWidget(self.chk_auto_updates)

        self.lbl_update_status = QLabel("Статус: нажмите «Проверить сейчас» для запроса последнего релиза с GitHub.")
        self.lbl_update_status.setStyleSheet("font-size: 12px; color: #94A3B8; font-weight: 600;")
        update_lay.addWidget(self.lbl_update_status)

        # Версионность и безопасный откат
        ver_mgmt_row = QHBoxLayout()
        ver_mgmt_row.setSpacing(10)
        installed_vers = VersionManager.get_installed_versions()
        self.lbl_ver_hist = QLabel(f"Установленные версии: {', '.join(['v' + v for v in installed_vers])} (Активна: v{VersionManager.get_active_version()})")
        self.lbl_ver_hist.setStyleSheet("font-size: 12px; color: #94A3B8;")

        self.btn_rollback = QPushButton("↩ Откатить на прошлую версию", objectName="SecondaryButton")
        self.btn_rollback.setIcon(get_svg_icon("refresh", color="#94A3B8"))
        self.btn_rollback.setMinimumHeight(28)
        self.btn_rollback.clicked.connect(self._on_rollback_clicked)
        self.btn_rollback.setVisible(len(installed_vers) > 1)

        ver_mgmt_row.addWidget(self.lbl_ver_hist, 1)
        ver_mgmt_row.addWidget(self.btn_rollback)
        update_lay.addLayout(ver_mgmt_row)

        layout.addWidget(self.update_card)

        # ==============================================================================
        # 3. КАРТОЧКА: ОБРАТНАЯ СВЯЗЬ И ПОДДЕРЖКА (FEEDBACK)
        # ==============================================================================
        self.feedback_card = HoverGlassCard()
        feedback_lay = QVBoxLayout(self.feedback_card)
        feedback_lay.setContentsMargins(24, 20, 24, 20)
        feedback_lay.setSpacing(14)

        fb_header_lay = QHBoxLayout()
        fb_header_lay.setSpacing(14)
        self.glass_fb_icon = GlassIconWidget("mail", accent, size=QSize(42, 42))
        fb_header_lay.addWidget(self.glass_fb_icon)

        fb_title_vbox = QVBoxLayout()
        fb_title_vbox.setSpacing(2)
        self.lbl_fb_head = QLabel("Обратная связь и техническая поддержка", objectName="SectionTitle")
        self.lbl_fb_head.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {accent};")
        
        self.lbl_fb_sub = QLabel(f"Отправка отзывов, предложений и сообщений об ошибках разработчику ({FEEDBACK_EMAIL})")
        self.lbl_fb_sub.setStyleSheet("font-size: 12px; color: #94A3B8;")
        
        fb_title_vbox.addWidget(self.lbl_fb_head)
        fb_title_vbox.addWidget(self.lbl_fb_sub)
        fb_header_lay.addLayout(fb_title_vbox, 1)
        feedback_lay.addLayout(fb_header_lay)

        # Информационная плашка с контактом и темой
        self.fb_info_box = HoverGlassCard()
        self.fb_info_box.setObjectName("FbInfoBox")
        fb_box_lay = QVBoxLayout(self.fb_info_box)
        fb_box_lay.setContentsMargins(16, 12, 16, 12)
        fb_box_lay.setSpacing(6)

        self.lbl_fb_email_title = QLabel("Контактный Email разработчика:")
        self.lbl_fb_email_val = QLabel(FEEDBACK_EMAIL)
        self.lbl_fb_email_val.setStyleSheet(f"color: {accent}; font-family: monospace; font-size: 14px; font-weight: bold;")
        self.lbl_fb_email_val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.lbl_fb_subj_val = QLabel(f"Автоматическая тема письма: {FEEDBACK_SUBJECT_TEMPLATE}")
        self.lbl_fb_subj_val.setStyleSheet("font-size: 12px; color: #94A3B8; font-weight: 500;")

        fb_box_lay.addWidget(self.lbl_fb_email_title)
        fb_box_lay.addWidget(self.lbl_fb_email_val)
        fb_box_lay.addWidget(self.lbl_fb_subj_val)
        feedback_lay.addWidget(self.fb_info_box)

        # Кнопки быстрых действий обратной связи
        fb_btns_lay = QHBoxLayout()
        fb_btns_lay.setSpacing(10)

        self.btn_fb_mailto = QPushButton("  Почтовый клиент", objectName="PrimaryButton")
        self.btn_fb_mailto.setIcon(get_svg_icon("mail", color="#FFFFFF" if is_light else "#020617"))
        self.btn_fb_mailto.setMinimumHeight(36)
        self.btn_fb_mailto.setStyleSheet("font-size: 13px; font-weight: 700;")
        self.btn_fb_mailto.clicked.connect(self._open_mailto)

        self.btn_fb_gmail = QPushButton("  Написать в Gmail", objectName="SecondaryButton")
        self.btn_fb_gmail.setIcon(get_svg_icon("external_link", color=accent))
        self.btn_fb_gmail.setMinimumHeight(36)
        self.btn_fb_gmail.setStyleSheet("font-size: 13px; font-weight: 600;")
        self.btn_fb_gmail.clicked.connect(self._open_gmail)

        self.btn_fb_mailru = QPushButton("  Написать в Mail.ru", objectName="SecondaryButton")
        self.btn_fb_mailru.setIcon(get_svg_icon("external_link", color=accent))
        self.btn_fb_mailru.setMinimumHeight(36)
        self.btn_fb_mailru.setStyleSheet("font-size: 13px; font-weight: 600;")
        self.btn_fb_mailru.clicked.connect(self._open_mailru)

        self.btn_fb_copy = QPushButton("  Скопировать шаблон", objectName="SecondaryButton")
        self.btn_fb_copy.setIcon(get_svg_icon("copy", color=accent))
        self.btn_fb_copy.setMinimumHeight(36)
        self.btn_fb_copy.setStyleSheet("font-size: 13px; font-weight: 600;")
        self.btn_fb_copy.clicked.connect(self._copy_feedback_template)

        fb_btns_lay.addWidget(self.btn_fb_mailto)
        fb_btns_lay.addWidget(self.btn_fb_gmail)
        fb_btns_lay.addWidget(self.btn_fb_mailru)
        fb_btns_lay.addWidget(self.btn_fb_copy)
        fb_btns_lay.addStretch()

        feedback_lay.addLayout(fb_btns_lay)
        layout.addWidget(self.feedback_card)

        # ==============================================================================
        # 4. КАРТОЧКА: КАСТОМИЗАЦИЯ 3D-ВОЛН
        # ==============================================================================
        self.wave_card = HoverGlassCard()
        wave_lay = QVBoxLayout(self.wave_card)
        wave_lay.setContentsMargins(24, 20, 24, 20)
        wave_lay.setSpacing(14)

        self.lbl_wave_head = QLabel("🌊 Редактор 3D-волн заднего плана (OpenGL)", objectName="SectionTitle")
        self.lbl_wave_head.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {accent};")
        wave_lay.addWidget(self.lbl_wave_head)

        wave_settings = QSettings("WaterMetrics", "WaveSettings")
        init_waves_enabled = wave_settings.value("WavesEnabled", True, type=bool)
        init_density = wave_settings.value("GridDensity", 30, type=int)
        init_opacity = wave_settings.value("LineOpacity", 28, type=int)
        init_amp = wave_settings.value("WaveAmplitude", 100, type=int)
        init_speed = wave_settings.value("WaveSpeed", 10, type=int)
        init_tilt = wave_settings.value("WaveTilt", 48, type=int)

        self.chk_enable_waves = QCheckBox("Отображать 3D-сетку волн (OpenGL background)")
        self.chk_enable_waves.setChecked(init_waves_enabled)
        self.chk_enable_waves.toggled.connect(self._on_waves_enabled_toggled)
        wave_lay.addWidget(self.chk_enable_waves)

        grid_wave = QGridLayout()
        grid_wave.setSpacing(12)

        # Плотность сетки (4 до 60 квадратов)
        self.lbl_density_t = QLabel("Плотность сетки (от 4×4):", objectName="FieldLabel")
        self.lbl_density_val = QLabel(f"{init_density} x {init_density}")
        self.lbl_density_val.setStyleSheet(f"color: {accent}; font-weight: bold;")
        self.sld_density = QSlider(Qt.Orientation.Horizontal)
        self.sld_density.setRange(4, 60)
        self.sld_density.setValue(init_density)
        self.sld_density.valueChanged.connect(self._on_density_changed)

        # Прозрачность линий (0% до 100% - можно полностью убрать)
        self.lbl_opacity_t = QLabel("Прозрачность линий (0% - полностью скрыть):", objectName="FieldLabel")
        self.lbl_opacity_val = QLabel(f"{init_opacity}%")
        self.lbl_opacity_val.setStyleSheet(f"color: {accent}; font-weight: bold;")
        self.sld_opacity = QSlider(Qt.Orientation.Horizontal)
        self.sld_opacity.setRange(0, 100)
        self.sld_opacity.setValue(init_opacity)
        self.sld_opacity.valueChanged.connect(self._on_opacity_changed)

        # Интенсивность / Амплитуда волн
        self.lbl_amp_t = QLabel("Интенсивность волн (высота):", objectName="FieldLabel")
        self.lbl_amp_val = QLabel(f"{init_amp}%")
        self.lbl_amp_val.setStyleSheet(f"color: {accent}; font-weight: bold;")
        self.sld_amp = QSlider(Qt.Orientation.Horizontal)
        self.sld_amp.setRange(0, 200)
        self.sld_amp.setValue(init_amp)
        self.sld_amp.valueChanged.connect(self._on_amp_changed)

        # Скорость движения волн
        self.lbl_speed_t = QLabel("Скорость анимации волн:", objectName="FieldLabel")
        self.lbl_speed_val = QLabel(f"{init_speed / 10.0:.1f}x")
        self.lbl_speed_val.setStyleSheet(f"color: {accent}; font-weight: bold;")
        self.sld_speed = QSlider(Qt.Orientation.Horizontal)
        self.sld_speed.setRange(0, 30)
        self.sld_speed.setValue(init_speed)
        self.sld_speed.valueChanged.connect(self._on_speed_changed)

        # Наклон сетки
        self.lbl_tilt_t = QLabel("Наклон 3D сетки:", objectName="FieldLabel")
        self.lbl_tilt_val = QLabel(f"{init_tilt}°")
        self.lbl_tilt_val.setStyleSheet(f"color: {accent}; font-weight: bold;")
        self.sld_tilt = QSlider(Qt.Orientation.Horizontal)
        self.sld_tilt.setRange(10, 90)
        self.sld_tilt.setValue(init_tilt)
        self.sld_tilt.valueChanged.connect(self._on_tilt_changed)

        grid_wave.addWidget(self.lbl_density_t, 0, 0)
        grid_wave.addWidget(self.sld_density, 0, 1)
        grid_wave.addWidget(self.lbl_density_val, 0, 2)

        grid_wave.addWidget(self.lbl_opacity_t, 1, 0)
        grid_wave.addWidget(self.sld_opacity, 1, 1)
        grid_wave.addWidget(self.lbl_opacity_val, 1, 2)

        grid_wave.addWidget(self.lbl_amp_t, 2, 0)
        grid_wave.addWidget(self.sld_amp, 2, 1)
        grid_wave.addWidget(self.lbl_amp_val, 2, 2)

        grid_wave.addWidget(self.lbl_speed_t, 3, 0)
        grid_wave.addWidget(self.sld_speed, 3, 1)
        grid_wave.addWidget(self.lbl_speed_val, 3, 2)

        grid_wave.addWidget(self.lbl_tilt_t, 4, 0)
        grid_wave.addWidget(self.sld_tilt, 4, 1)
        grid_wave.addWidget(self.lbl_tilt_val, 4, 2)

        wave_lay.addLayout(grid_wave)
        layout.addWidget(self.wave_card)

        # ==============================================================================
        # 5. КАРТОЧКА: ВИДИМОСТЬ ЭЛЕМЕНТОВ ИНТЕРФЕЙСА (МИНИМАЛИЗМ)
        # ==============================================================================
        self.vis_card = HoverGlassCard()
        vis_lay = QVBoxLayout(self.vis_card)
        vis_lay.setContentsMargins(24, 20, 24, 20)
        vis_lay.setSpacing(14)

        self.lbl_vis_head = QLabel("👁 Отображение элементов Главного экрана (Минимализм)", objectName="SectionTitle")
        self.lbl_vis_head.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {accent};")
        vis_lay.addWidget(self.lbl_vis_head)

        grid_vis = QGridLayout()
        grid_vis.setSpacing(12)

        ui_vis_settings = QSettings("WaterMetrics", "UIVisibility")

        self.chk_vis_kpi = QCheckBox("Панель KPI метрик расхода")
        self.chk_vis_kpi.setChecked(ui_vis_settings.value("VisKPI", True, type=bool))
        self.chk_vis_kpi.toggled.connect(self._toggle_kpi_visibility)

        self.chk_vis_files = QCheckBox("Карточка загрузки файлов (Шаблон / Аркус)")
        self.chk_vis_files.setChecked(ui_vis_settings.value("VisFiles", True, type=bool))
        self.chk_vis_files.toggled.connect(self._toggle_files_visibility)

        self.chk_vis_targets = QCheckBox("Карточка параметров ХВС / ГВС / ДОБ.")
        self.chk_vis_targets.setChecked(ui_vis_settings.value("VisTargets", True, type=bool))
        self.chk_vis_targets.toggled.connect(self._toggle_targets_visibility)

        self.chk_vis_hist = QCheckBox("Карточка истории сгенерированных отчетов")
        self.chk_vis_hist.setChecked(ui_vis_settings.value("VisHist", True, type=bool))
        self.chk_vis_hist.toggled.connect(self._toggle_hist_visibility)

        self.chk_vis_control = QCheckBox("Нижняя плавающая панель запуска расчетов")
        self.chk_vis_control.setChecked(ui_vis_settings.value("VisControl", True, type=bool))
        self.chk_vis_control.toggled.connect(self._toggle_control_visibility)

        self.chk_vis_title = QCheckBox("Верхняя панель кастомного заголовка окна")
        self.chk_vis_title.setChecked(ui_vis_settings.value("VisTitle", True, type=bool))
        self.chk_vis_title.toggled.connect(self._toggle_title_visibility)

        grid_vis.addWidget(self.chk_vis_kpi, 0, 0)
        grid_vis.addWidget(self.chk_vis_files, 0, 1)
        grid_vis.addWidget(self.chk_vis_targets, 1, 0)
        grid_vis.addWidget(self.chk_vis_hist, 1, 1)
        grid_vis.addWidget(self.chk_vis_control, 2, 0)
        grid_vis.addWidget(self.chk_vis_title, 2, 1)

        vis_lay.addLayout(grid_vis)
        layout.addWidget(self.vis_card)

        scroll.setWidget(scroll_content)
        root_layout.addWidget(scroll, 1)

        ThemeManager.on_theme_changed.append(self.update_theme_elements)
        self.update_theme_elements()

    def showEvent(self, event):
        super().showEvent(event)
        self.update_theme_elements()

    def update_theme_elements(self, theme_name: str = None):
        """Динамическое применение стилей, цветов и контраста для всех тем."""
        curr_theme = theme_name or ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        accent = ThemeManager.get_current_accent_color()

        # Цветовые константы под текущую тему
        if curr_theme == "Как дома":
            title_col = "#0A246A"
            head_col = "#0A246A"
            sub_col = "#475569"
            label_col = "#1E293B"
            chk_col = "#0A246A"
            input_bg = "#FFFFFF"
            input_border = "#7F9DB9"
            input_text = "#000000"
            box_bg = "rgba(10, 36, 106, 0.04)"
            box_border = "#7F9DB9"
        elif curr_theme == "Pearl Light":
            title_col = "#0F172A"
            head_col = "#028090"
            sub_col = "#475569"
            label_col = "#1E293B"
            chk_col = "#028090"
            input_bg = "#FFFFFF"
            input_border = "rgba(2, 128, 144, 0.35)"
            input_text = "#0F172A"
            box_bg = "rgba(2, 128, 144, 0.05)"
            box_border = "rgba(2, 128, 144, 0.25)"
        else:
            title_col = "#F8FAFC"
            head_col = accent
            sub_col = "#94A3B8"
            label_col = "#E2E8F0"
            chk_col = accent
            input_bg = "rgba(255, 255, 255, 0.06)"
            input_border = "rgba(255, 255, 255, 0.18)"
            input_text = "#F8FAFC"
            box_bg = "rgba(255, 255, 255, 0.03)"
            box_border = "rgba(255, 255, 255, 0.08)"

        # Иконки
        if hasattr(self, 'glass_app_icon'):
            self.glass_app_icon.set_color(accent)
        if hasattr(self, 'glass_upd_icon'):
            self.glass_upd_icon.set_color(accent)
        if hasattr(self, 'glass_fb_icon'):
            self.glass_fb_icon.set_color(accent)

        # Главный заголовок
        if hasattr(self, 'main_title'):
            self.main_title.setStyleSheet(f"color: {title_col}; font-size: 20px; font-weight: 700;")

        # Заголовки разделов
        if hasattr(self, 'appName_label'):
            app_title_col = "#0A246A" if curr_theme == "Как дома" else ("#0F172A" if curr_theme == "Pearl Light" else accent)
            self.appName_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {app_title_col};")
        if hasattr(self, 'appSub_label'):
            self.appSub_label.setStyleSheet(f"font-size: 13px; color: {sub_col};")
        if hasattr(self, 'appVer_label'):
            self.appVer_label.setStyleSheet(f"font-size: 12px; color: {sub_col}; font-weight: 600;")

        for h_name in ('lbl_upd_head', 'lbl_fb_head', 'lbl_wave_head', 'lbl_vis_head'):
            if hasattr(self, h_name):
                getattr(self, h_name).setStyleSheet(f"font-size: 16px; font-weight: 700; color: {head_col};")

        for s_name in ('lbl_upd_sub', 'lbl_fb_sub'):
            if hasattr(self, s_name):
                getattr(self, s_name).setStyleSheet(f"font-size: 12px; color: {sub_col};")

        if hasattr(self, 'lbl_repo'):
            self.lbl_repo.setStyleSheet(f"font-size: 12px; color: {label_col}; font-weight: 600;")

        if hasattr(self, 'txt_repo'):
            self.txt_repo.setStyleSheet(f"""
                QLineEdit {{
                    background: {input_bg};
                    color: {input_text};
                    border: 1px solid {input_border};
                    border-radius: 8px;
                    padding: 4px 10px;
                    font-size: 12px;
                }}
                QLineEdit:focus {{
                    border: 1.5px solid {accent};
                }}
            """)

        # Чекбоксы
        chk_style = f"""
            QCheckBox {{
                color: {label_col};
                font-weight: 600;
                font-size: 13px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid {input_border};
                background: {input_bg};
            }}
            QCheckBox::indicator:checked {{
                background: {accent};
                border-color: {accent};
            }}
        """
        for chk_name in ('chk_auto_updates', 'chk_enable_waves', 'chk_vis_kpi', 'chk_vis_files',
                         'chk_vis_targets', 'chk_vis_hist', 'chk_vis_control', 'chk_vis_title'):
            if hasattr(self, chk_name):
                getattr(self, chk_name).setStyleSheet(chk_style)

        # Слайдеры и подписи
        for l_name in ('lbl_density_t', 'lbl_opacity_t', 'lbl_amp_t', 'lbl_speed_t', 'lbl_tilt_t'):
            if hasattr(self, l_name):
                getattr(self, l_name).setStyleSheet(f"color: {label_col}; font-size: 12px; font-weight: 600;")

        for v_name in ('lbl_density_val', 'lbl_opacity_val', 'lbl_amp_val', 'lbl_speed_val', 'lbl_tilt_val'):
            if hasattr(self, v_name):
                getattr(self, v_name).setStyleSheet(f"color: {chk_col}; font-weight: bold; font-size: 12px;")

        # Блок обратной связи
        if hasattr(self, 'fb_info_box'):
            self.fb_info_box.setStyleSheet(f"""
                QFrame#FbInfoBox {{
                    background: {box_bg};
                    border: 1px solid {box_border};
                    border-radius: 12px;
                }}
                QFrame#FbInfoBox:hover, QFrame#FbInfoBox[hover="true"] {{
                    background: {box_bg};
                    border: 1px solid {box_border};
                }}
            """)
        if hasattr(self, 'lbl_fb_email_title'):
            self.lbl_fb_email_title.setStyleSheet(f"color: {sub_col}; font-size: 12px; font-weight: 500;")
        if hasattr(self, 'lbl_fb_email_val'):
            self.lbl_fb_email_val.setStyleSheet(f"color: {chk_col}; font-family: monospace; font-size: 14px; font-weight: bold;")
        if hasattr(self, 'lbl_fb_subj_val'):
            self.lbl_fb_subj_val.setStyleSheet(f"color: {label_col}; font-size: 12px; font-weight: 500;")

        # Стили кнопок обновлений и навигации (Высокая контрастность, читаемость в любых темах)
        if curr_theme == "Как дома":
            primary_btn_style = """
                QPushButton {
                    background-color: #0A246A;
                    color: #FFFFFF;
                    font-weight: bold;
                    font-size: 12px;
                    border: 1px solid #000000;
                    border-radius: 3px;
                    padding: 6px 16px;
                    min-height: 24px;
                }
                QPushButton:hover {
                    background-color: #163988;
                }
                QPushButton:disabled {
                    background-color: #A0A0A0;
                    color: #D0D0D0;
                }
            """
            secondary_btn_style = """
                QPushButton {
                    background-color: #D4D0C8;
                    color: #000000;
                    font-weight: 500;
                    font-size: 12px;
                    border: 1px solid #7F9DB9;
                    border-radius: 3px;
                    padding: 6px 12px;
                    min-height: 24px;
                }
                QPushButton:hover {
                    background-color: #ECE9D8;
                }
            """
            btn_text_color = "#FFFFFF"
        elif curr_theme == "Pearl Light":
            primary_btn_style = """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #028090, stop:1 #00A896);
                    color: #FFFFFF;
                    font-weight: 700;
                    font-size: 13px;
                    border: none;
                    border-radius: 10px;
                    padding: 8px 18px;
                    min-height: 24px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00A896, stop:1 #028090);
                }
                QPushButton:disabled {
                    background: #CBD5E1;
                    color: #94A3B8;
                }
            """
            secondary_btn_style = """
                QPushButton {
                    background-color: #F1F5F9;
                    color: #0F172A;
                    font-weight: 600;
                    font-size: 13px;
                    border: 1px solid #CBD5E1;
                    border-radius: 10px;
                    padding: 7px 14px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: #E2E8F0;
                    border-color: #028090;
                    color: #028090;
                }
            """
            btn_text_color = "#FFFFFF"
        elif curr_theme == "Cyberpunk Neon":
            primary_btn_style = """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF007F, stop:1 #9D00FF);
                    color: #FFFFFF;
                    font-weight: 700;
                    font-size: 13px;
                    border: 1px solid #FF007F;
                    border-radius: 10px;
                    padding: 8px 18px;
                    min-height: 24px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF1493, stop:1 #B026FF);
                    border-color: #00F2FE;
                }
                QPushButton:disabled {
                    background: rgba(36, 5, 54, 0.6);
                    color: #64748B;
                    border-color: rgba(255, 0, 127, 0.3);
                }
            """
            secondary_btn_style = """
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.08);
                    color: #F8FAFC;
                    font-weight: 600;
                    font-size: 13px;
                    border: 1px solid rgba(255, 0, 127, 0.35);
                    border-radius: 10px;
                    padding: 7px 14px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 0, 127, 0.18);
                    border-color: #FF007F;
                    color: #FF007F;
                }
            """
            btn_text_color = "#FFFFFF"
        elif curr_theme == "Emerald Cyber":
            primary_btn_style = """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10B981);
                    color: #020617;
                    font-weight: 700;
                    font-size: 13px;
                    border: 1px solid #10B981;
                    border-radius: 10px;
                    padding: 8px 18px;
                    min-height: 24px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #34D399);
                }
                QPushButton:disabled {
                    background: rgba(6, 38, 24, 0.6);
                    color: #64748B;
                    border-color: rgba(16, 185, 129, 0.3);
                }
            """
            secondary_btn_style = """
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.08);
                    color: #F8FAFC;
                    font-weight: 600;
                    font-size: 13px;
                    border: 1px solid rgba(16, 185, 129, 0.35);
                    border-radius: 10px;
                    padding: 7px 14px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: rgba(16, 185, 129, 0.18);
                    border-color: #10B981;
                    color: #10B981;
                }
            """
            btn_text_color = "#020617"
        elif curr_theme == "Deep Violet Glass":
            primary_btn_style = """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7C3AED, stop:1 #A855F7);
                    color: #FFFFFF;
                    font-weight: 700;
                    font-size: 13px;
                    border: 1px solid #A855F7;
                    border-radius: 10px;
                    padding: 8px 18px;
                    min-height: 24px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8B5CF6, stop:1 #C084FC);
                }
                QPushButton:disabled {
                    background: rgba(24, 10, 56, 0.6);
                    color: #64748B;
                    border-color: rgba(168, 85, 247, 0.3);
                }
            """
            secondary_btn_style = """
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.08);
                    color: #F8FAFC;
                    font-weight: 600;
                    font-size: 13px;
                    border: 1px solid rgba(168, 85, 247, 0.35);
                    border-radius: 10px;
                    padding: 7px 14px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: rgba(168, 85, 247, 0.18);
                    border-color: #A855F7;
                    color: #A855F7;
                }
            """
            btn_text_color = "#FFFFFF"
        else: # Dark Tech Azure
            primary_btn_style = """
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #028090, stop:0.5 #00A896, stop:1 #00F2FE);
                    color: #020617;
                    font-weight: 700;
                    font-size: 13px;
                    border: 1px solid #00F2FE;
                    border-radius: 10px;
                    padding: 8px 18px;
                    min-height: 24px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00A896, stop:1 #00F2FE);
                    border-color: #FFFFFF;
                }
                QPushButton:disabled {
                    background: rgba(30, 41, 59, 0.6);
                    color: #64748B;
                    border-color: rgba(0, 242, 254, 0.2);
                }
            """
            secondary_btn_style = """
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.08);
                    color: #F8FAFC;
                    font-weight: 600;
                    font-size: 13px;
                    border: 1px solid rgba(255, 255, 255, 0.15);
                    border-radius: 10px;
                    padding: 7px 14px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.16);
                    border-color: #00F2FE;
                    color: #00F2FE;
                }
            """
            btn_text_color = "#020617"

        # Кнопки
        if hasattr(self, 'btn_check_update'):
            self.btn_check_update.setStyleSheet(primary_btn_style)
            self.btn_check_update.setIcon(get_svg_icon("update", color=btn_text_color))
        if hasattr(self, 'btn_card_check'):
            self.btn_card_check.setStyleSheet(primary_btn_style)
            self.btn_card_check.setIcon(get_svg_icon("update", color=btn_text_color))
            self.btn_card_check.setMinimumWidth(160)
        if hasattr(self, 'btn_fb_mailto'):
            self.btn_fb_mailto.setStyleSheet(primary_btn_style)
            self.btn_fb_mailto.setIcon(get_svg_icon("mail", color=btn_text_color))

        for sec_name in ('btn_welcome_setup', 'btn_onboarding', 'btn_feedback', 'btn_donate'):
            if hasattr(self, sec_name):
                getattr(self, sec_name).setStyleSheet(secondary_btn_style)

        if hasattr(self, 'btn_fb_gmail'):
            self.btn_fb_gmail.setIcon(get_svg_icon("external_link", color=chk_col))
        if hasattr(self, 'btn_fb_mailru'):
            self.btn_fb_mailru.setIcon(get_svg_icon("external_link", color=chk_col))
        if hasattr(self, 'btn_fb_copy'):
            self.btn_fb_copy.setIcon(get_svg_icon("copy", color=chk_col))
        if hasattr(self, 'btn_feedback'):
            self.btn_feedback.setIcon(get_svg_icon("mail", color=chk_col))
        if hasattr(self, 'btn_donate'):
            self.btn_donate.setIcon(get_svg_icon("about", color=chk_col))

        if hasattr(self, 'btn_beach'):
            if curr_theme == "Как дома":
                self.btn_beach.setStyleSheet("QPushButton#AccentButton { background-color: #005A9E; color: #FFFFFF; font-weight: bold; font-size: 12px; border: 1px solid #003D7A; border-radius: 3px; padding: 6px 14px; min-height: 22px; } QPushButton#AccentButton:hover { background-color: #0068B4; }")
                self.btn_beach.setIcon(get_svg_icon("run", color="#FFFFFF"))
            elif curr_theme == "Pearl Light":
                self.btn_beach.setStyleSheet("QPushButton#AccentButton { background-color: #028090; color: #FFFFFF; font-weight: bold; font-size: 12px; border: none; border-radius: 10px; padding: 6px 14px; min-height: 22px; } QPushButton#AccentButton:hover { background-color: #026C7A; }")
                self.btn_beach.setIcon(get_svg_icon("run", color="#FFFFFF"))
            else:
                self.btn_beach.setStyleSheet("")
                self.btn_beach.setIcon(get_svg_icon("run", color="#020617"))

        # Карточки GlassCard под все 6 тем (базовый фон, фон при наведении, рамка, скругление)
        card_bgs = {
            "Dark Tech Azure": ("#0B1736", "#0F2048", "#00F2FE", "18px"),
            "Cyberpunk Neon": ("#240536", "#300748", "#FF007F", "18px"),
            "Emerald Cyber": ("#062618", "#093320", "#10B981", "18px"),
            "Deep Violet Glass": ("#180A38", "#250F52", "#A855F7", "18px"),
            "Pearl Light": ("#F8FAFC", "#FFFFFF", "#028090", "18px"),
            "Как дома": ("#FFFFFF", "#F8FAFC", "#7F9DB9", "2px"),
        }
        bg, bg_hover, border, rad = card_bgs.get(curr_theme, ("#0B1736", "#0F2048", accent, "18px"))
        card_style = f"""
            QFrame#GlassCard {{
                background-color: {bg};
                border: 1.5px solid {border};
                border-radius: {rad};
            }}
            QFrame#GlassCard:hover, QFrame#GlassCard[hover="true"] {{
                background-color: {bg_hover};
                border: 1.5px solid {border};
                border-radius: {rad};
            }}
        """

        for card_name in ('info_card', 'update_card', 'feedback_card', 'wave_card', 'vis_card'):
            if hasattr(self, card_name):
                c = getattr(self, card_name)
                c.setStyleSheet(card_style)
                c.style().unpolish(c)
                c.style().polish(c)
                c.update()

    def _open_mailto(self):
        subject_enc = urllib.parse.quote(FEEDBACK_SUBJECT_TEMPLATE)
        body_enc = urllib.parse.quote(FEEDBACK_BODY_TEMPLATE)
        url = f"mailto:{FEEDBACK_EMAIL}?subject={subject_enc}&body={body_enc}"
        QDesktopServices.openUrl(QUrl(url))
        ToastNotification.show_toast(self, "Запущен системный почтовый клиент!", "SUCCESS")

    def _open_gmail(self):
        subject_enc = urllib.parse.quote(FEEDBACK_SUBJECT_TEMPLATE)
        body_enc = urllib.parse.quote(FEEDBACK_BODY_TEMPLATE)
        url = f"https://mail.google.com/mail/?view=cm&fs=1&to={FEEDBACK_EMAIL}&su={subject_enc}&body={body_enc}"
        QDesktopServices.openUrl(QUrl(url))
        ToastNotification.show_toast(self, "Открываем веб-интерфейс Gmail...", "INFO")

    def _open_mailru(self):
        subject_enc = urllib.parse.quote(FEEDBACK_SUBJECT_TEMPLATE)
        body_enc = urllib.parse.quote(FEEDBACK_BODY_TEMPLATE)
        url = f"https://e.mail.ru/compose/?to={FEEDBACK_EMAIL}&subject={subject_enc}&body={body_enc}"
        QDesktopServices.openUrl(QUrl(url))
        ToastNotification.show_toast(self, "Открываем веб-интерфейс Mail.ru...", "INFO")

    def _copy_feedback_template(self):
        full_text = f"Кому: {FEEDBACK_EMAIL}\nТема: {FEEDBACK_SUBJECT_TEMPLATE}\n\n{FEEDBACK_BODY_TEMPLATE}"
        QApplication.clipboard().setText(full_text)
        ToastNotification.show_toast(self, "Email, тема и образец письма скопированы!", "SUCCESS")

    def show_feedback_dialog(self):
        dlg = FeedbackDialog(self)
        dlg.exec()

    def _get_ocean(self):
        win = self.window()
        if win and hasattr(win, 'ocean_bg'):
            return win.ocean_bg
        return None

    def _get_page_main(self):
        win = self.window()
        if win and hasattr(win, 'page_main'):
            return win.page_main
        return None

    def _on_waves_enabled_toggled(self, enabled: bool):
        ocean = self._get_ocean()
        if ocean and hasattr(ocean, 'set_waves_enabled'):
            ocean.set_waves_enabled(enabled)
        else:
            QSettings("WaterMetrics", "WaveSettings").setValue("WavesEnabled", enabled)

    def _on_density_changed(self, val: int):
        self.lbl_density_val.setText(f"{val} x {val}")
        ocean = self._get_ocean()
        if ocean and hasattr(ocean, 'set_grid_density'):
            ocean.set_grid_density(val)
        else:
            QSettings("WaterMetrics", "WaveSettings").setValue("GridDensity", val)

    def _on_opacity_changed(self, val: int):
        self.lbl_opacity_val.setText(f"{val}%")
        ocean = self._get_ocean()
        if ocean and hasattr(ocean, 'set_user_opacity_percent'):
            ocean.set_user_opacity_percent(val)
        elif ocean and hasattr(ocean, 'set_line_opacity'):
            ocean.set_line_opacity((val / 100.0) * 0.40)
        else:
            QSettings("WaterMetrics", "WaveSettings").setValue("LineOpacity", val)

    def _on_amp_changed(self, val: int):
        self.lbl_amp_val.setText(f"{val}%")
        ocean = self._get_ocean()
        if ocean and hasattr(ocean, 'set_wave_amplitude'):
            ocean.set_wave_amplitude((val / 100.0) * 0.22)
        else:
            QSettings("WaterMetrics", "WaveSettings").setValue("WaveAmplitude", val)

    def _on_speed_changed(self, val: int):
        spd = val / 10.0
        self.lbl_speed_val.setText(f"{spd:.1f}x")
        ocean = self._get_ocean()
        if ocean and hasattr(ocean, 'set_speed_scale'):
            ocean.set_speed_scale(spd)
        else:
            QSettings("WaterMetrics", "WaveSettings").setValue("WaveSpeed", val)

    def _on_tilt_changed(self, val: int):
        self.lbl_tilt_val.setText(f"{val}°")
        ocean = self._get_ocean()
        if ocean and hasattr(ocean, 'set_tilt'):
            ocean.set_tilt(val * 0.01)
        else:
            QSettings("WaterMetrics", "WaveSettings").setValue("WaveTilt", val)

    def _toggle_kpi_visibility(self, visible: bool):
        p = self._get_page_main()
        if p and hasattr(p, 'kpi_container'):
            p.kpi_container.setVisible(visible)
        QSettings("WaterMetrics", "UIVisibility").setValue("VisKPI", visible)

    def _toggle_files_visibility(self, visible: bool):
        p = self._get_page_main()
        if p and hasattr(p, 'card_files'):
            p.card_files.setVisible(visible)
        QSettings("WaterMetrics", "UIVisibility").setValue("VisFiles", visible)

    def _toggle_targets_visibility(self, visible: bool):
        p = self._get_page_main()
        if p and hasattr(p, 'card_targets'):
            p.card_targets.setVisible(visible)
        QSettings("WaterMetrics", "UIVisibility").setValue("VisTargets", visible)

    def _toggle_hist_visibility(self, visible: bool):
        p = self._get_page_main()
        if p and hasattr(p, 'card_hist'):
            p.card_hist.setVisible(visible)
        QSettings("WaterMetrics", "UIVisibility").setValue("VisHist", visible)

    def _toggle_control_visibility(self, visible: bool):
        p = self._get_page_main()
        if p and hasattr(p, 'control_panel'):
            p.control_panel.setVisible(visible)
        QSettings("WaterMetrics", "UIVisibility").setValue("VisControl", visible)

    def _toggle_title_visibility(self, visible: bool):
        win = self.window()
        if win and hasattr(win, 'title_bar'):
            win.title_bar.setVisible(visible)
        QSettings("WaterMetrics", "UIVisibility").setValue("VisTitle", visible)

    def show_donate(self):
        dlg = DonateDialog(self)
        dlg.exec()

    def show_beach(self):
        gif_path = get_asset_path("beach.gif")
        dlg = BeachRestDialog(gif_path, self)
        dlg.exec()

    def _on_repo_text_changed(self, text: str):
        cleaned = text.strip()
        QSettings("WaterMetrics", "Updates").setValue("GitHubRepo", cleaned)

    def _on_auto_check_toggled(self, checked: bool):
        QSettings("WaterMetrics", "Updates").setValue("AutoCheckUpdates", checked)

    def check_updates(self, silent: bool = False):
        """Запуск проверки обновлений на GitHub."""
        repo = self.txt_repo.text().strip() if hasattr(self, 'txt_repo') else DEFAULT_GITHUB_REPO
        if not repo:
            repo = DEFAULT_GITHUB_REPO

        self._silent_check = silent
        if not silent:
            if hasattr(self, 'btn_check_update'):
                self.btn_check_update.setEnabled(False)
                self.btn_check_update.setText("⏳ Проверка...")
            if hasattr(self, 'btn_card_check'):
                self.btn_card_check.setEnabled(False)
                self.btn_card_check.setText("⏳ Проверка...")

        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        status_info_col = "#028090" if is_light else "#00F2FE"

        if hasattr(self, 'lbl_update_status'):
            self.lbl_update_status.setText("Проверка наличия обновлений...")
            self.lbl_update_status.setStyleSheet(f"font-size: 12px; color: {status_info_col}; font-weight: 600;")

        self.update_checker = GitHubUpdateChecker(repo=repo, current_ver=APP_VERSION, parent=self)
        self.update_checker.update_available.connect(self._on_update_available)
        self.update_checker.already_latest.connect(self._on_already_latest)
        self.update_checker.check_failed.connect(self._on_check_failed)
        self.update_checker.start()

    @Slot(object)
    def _on_update_available(self, release_info: GitHubReleaseInfo):
        if hasattr(self, 'btn_check_update'):
            self.btn_check_update.setEnabled(True)
            self.btn_check_update.setText("Проверить обновления")
        if hasattr(self, 'btn_card_check'):
            self.btn_card_check.setEnabled(True)
            self.btn_card_check.setText("Проверить сейчас")

        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        avail_col = "#028090" if is_light else "#00d890"

        if hasattr(self, 'lbl_update_status'):
            self.lbl_update_status.setText(f"🔥 Доступна новая версия v{release_info.version}!")
            self.lbl_update_status.setStyleSheet(f"font-size: 12px; color: {avail_col}; font-weight: bold;")

        dlg = UpdateDialog(release_info, self.window() or self)
        dlg.exec()

    @Slot(str)
    def _on_already_latest(self, ver: str):
        if hasattr(self, 'btn_check_update'):
            self.btn_check_update.setEnabled(True)
            self.btn_check_update.setText("Проверить обновления")
        if hasattr(self, 'btn_card_check'):
            self.btn_card_check.setEnabled(True)
            self.btn_card_check.setText("Проверить сейчас")

        if hasattr(self, 'lbl_update_status'):
            self.lbl_update_status.setText(f"✅ У вас установлена самая свежая версия v{ver}")
            self.lbl_update_status.setStyleSheet("font-size: 12px; color: #10B981; font-weight: 600;")

        if not getattr(self, '_silent_check', False):
            ToastNotification.show_toast(self.window() or self, f"WaterMetrics v{ver} — установлена последняя версия!", "SUCCESS")

    @Slot(str)
    def _on_check_failed(self, err_msg: str):
        if hasattr(self, 'btn_check_update'):
            self.btn_check_update.setEnabled(True)
            self.btn_check_update.setText("Проверить обновления")
        if hasattr(self, 'btn_card_check'):
            self.btn_card_check.setEnabled(True)
            self.btn_card_check.setText("Проверить сейчас")

        if hasattr(self, 'lbl_update_status'):
            self.lbl_update_status.setText(f"⚠️ {err_msg}")
            self.lbl_update_status.setStyleSheet("font-size: 12px; color: #EF4444; font-weight: 600;")

        if not getattr(self, '_silent_check', False):
            ToastNotification.show_toast(self.window() or self, f"Проверка обновлений: {err_msg}", "ERROR")

    def restart_onboarding(self):
        """Перезапуск интерактивного обучения первой проводке."""
        win = self.window()
        if win and hasattr(win, 'start_onboarding'):
            win.start_onboarding(force=True)

    def show_welcome_setup(self):
        """Вызов мастера первичной настройки стилей, языка и 3D-волн."""
        win = getattr(self, 'main_win', None) or self.window()
        dlg = WelcomeSetupDialog(win, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if getattr(dlg, 'start_onboarding_requested', False) and win and hasattr(win, 'start_onboarding'):
                win.start_onboarding(force=True)

    def _on_rollback_clicked(self):
        """Выполняет откат на предыдущую локальную версию."""
        installed = VersionManager.get_installed_versions()
        if len(installed) <= 1:
            ToastNotification.show_toast(self, "Предыдущих версий не найдено", "INFO")
            return

        fallback = VersionManager.rollback_to_previous_version()
        if fallback:
            ToastNotification.show_toast(self, f"Откат на v{fallback} выполнен! Перезапустите приложение.", "SUCCESS")
            if hasattr(self, 'lbl_ver_hist'):
                self.lbl_ver_hist.setText(f"Установленные версии: {', '.join(['v' + v for v in VersionManager.get_installed_versions()])} (Активна: v{fallback})")
            if hasattr(self, 'btn_rollback'):
                self.btn_rollback.setVisible(len(VersionManager.get_installed_versions()) > 1)
