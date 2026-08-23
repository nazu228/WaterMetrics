import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QPushButton, QSplitter, QStackedWidget,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit,
    QCheckBox, QGraphicsDropShadowEffect, QStatusBar, QProgressBar
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor

# ==============================================================================
# QSS DESIGN SYSTEM: OCEANIC GLASS PREMIUM (STRICT CONTRAST)
# ==============================================================================
OCEANIC_GLASS_QSS = """
/* Главный фон приложения */
QMainWindow, QWidget#MainContainer {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F0F7F9, stop:1 #FBF8F1);
    font-family: "Segoe UI", "Inter", sans-serif;
}

QWidget {
    font-family: "Segoe UI", "Inter", sans-serif;
    color: #0F172A;
}

/* Стеклянные карточки */
QFrame#GlassCard {
    background-color: rgba(255, 255, 255, 0.90);
    border: 1px solid #CBD5E1;
    border-radius: 12px;
}

/* Боковая панель */
QFrame#SidebarPanel {
    background-color: #FFFFFF;
    border-right: 1px solid #CBD5E1;
}

/* Поля ввода */
QLineEdit {
    background-color: #FFFFFF;
    border: 1.5px solid #CBD5E1;
    border-radius: 8px;
    padding: 8px 12px;
    color: #0F172A;
    font-size: 13px;
    selection-background-color: #028090;
    selection-color: #FFFFFF;
}
QLineEdit:focus {
    border: 2px solid #028090;
}

/* Главная Кнопка (CTA) */
QPushButton#PrimaryButton {
    background-color: #028090;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 14px;
    border-radius: 8px;
    padding: 10px 20px;
    border: none;
    min-height: 24px;
}
QPushButton#PrimaryButton:hover {
    background-color: #00A896;
}
QPushButton#PrimaryButton:pressed {
    background-color: #05668D;
}
QPushButton#PrimaryButton:disabled {
    background-color: #CBD5E1;
    color: #64748B;
}

/* Вторичные Кнопки (Обзор, Очистить, Открыть и т.д.) */
QPushButton#SecondaryButton {
    background-color: #F8FAFC;
    color: #0F172A;
    font-weight: 600;
    font-size: 13px;
    border: 1px solid #94A3B8;
    border-radius: 8px;
    padding: 7px 14px;
    min-height: 20px;
}
QPushButton#SecondaryButton:hover {
    background-color: #E2E8F0;
    border-color: #028090;
    color: #028090;
}
QPushButton#SecondaryButton:pressed {
    background-color: #CBD5E1;
}
QPushButton#SecondaryButton:disabled {
    background-color: #F1F5F9;
    color: #94A3B8;
    border-color: #E2E8F0;
}

/* Акцентная кнопка (Мастер замен) */
QPushButton#AccentButton {
    background-color: #00A896;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 13px;
    border-radius: 8px;
    padding: 8px 16px;
    border: none;
    min-height: 22px;
}
QPushButton#AccentButton:hover {
    background-color: #02C39A;
}
QPushButton#AccentButton:pressed {
    background-color: #008A7B;
}

/* Опасная кнопка (Удаление) */
QPushButton#DangerButton {
    background-color: #EF4444;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 13px;
    border-radius: 8px;
    padding: 7px 14px;
    border: none;
    min-height: 20px;
}
QPushButton#DangerButton:hover {
    background-color: #DC2626;
}

/* Кнопки навигации Sidebar */
QPushButton.navBtn {
    background-color: transparent;
    color: #475569;
    text-align: left;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    border: none;
}
QPushButton.navBtn:hover {
    background-color: #F0F7F9;
    color: #028090;
}
QPushButton.navBtn:checked {
    background-color: #E6F4F1;
    color: #028090;
    font-weight: bold;
    border-left: 4px solid #028090;
}

/* Заголовки и Метки */
QLabel {
    color: #0F172A;
    font-size: 13px;
}
QLabel#PageTitle {
    color: #0F172A;
    font-size: 22px;
    font-weight: bold;
}
QLabel#SectionTitle {
    color: #0F172A;
    font-size: 16px;
    font-weight: bold;
}
QLabel#FieldLabel {
    color: #334155;
    font-size: 13px;
    font-weight: 600;
}

/* Таблицы */
QTableWidget {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    gridline-color: #E2E8F0;
}
QTableWidget::item {
    color: #0F172A;
    padding: 6px;
}
QTableWidget::item:selected {
    background-color: #E6F4F1;
    color: #028090;
}
QHeaderView::section {
    background-color: #F8FAFC;
    color: #0F172A;
    padding: 8px;
    font-weight: bold;
    font-size: 13px;
    border: none;
    border-bottom: 2px solid #CBD5E1;
    min-height: 28px;
}

/* Чекбоксы */
QCheckBox {
    color: #0F172A;
    font-size: 13px;
    font-weight: 600;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1.5px solid #94A3B8;
    border-radius: 4px;
    background-color: #FFFFFF;
}
QCheckBox::indicator:checked {
    background-color: #028090;
    border-color: #028090;
}

/* Консоли / Логи */
QTextEdit#LogViewer {
    background-color: #0F172A;
    color: #F8FAFC;
    border-radius: 8px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 10px;
    border: 1px solid #1E293B;
}

/* Разделитель QSplitter */
QSplitter::handle {
    background-color: #CBD5E1;
    width: 1px;
}

/* StatusBar */
QStatusBar {
    background-color: #FFFFFF;
    border-top: 1px solid #CBD5E1;
    color: #475569;
}
QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #E2E8F0;
    max-height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #028090;
    border-radius: 4px;
}
"""


# ==============================================================================
# HELPER: VOLUMETRIC SHADOW EFFECT
# ==============================================================================
def apply_oceanic_shadow(widget: QWidget, blur: int = 20, offset_y: int = 6, alpha: int = 25):
    """Применяет объемную мягкую тень к карточкам и кнопкам."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setColor(QColor(15, 23, 42, alpha))
    shadow.setOffset(0, offset_y)
    widget.setGraphicsEffect(shadow)


# ==============================================================================
# COLLAPSIBLE SIDEBAR
# ==============================================================================
class CollapsibleSidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarPanel")
        self.is_collapsed = False
        self.expanded_width = 220
        self.collapsed_width = 60

        self.setFixedWidth(self.expanded_width)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 16, 10, 16)
        layout.setSpacing(8)

        # Шапка с логотипом и переключателем
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 0, 4, 10)

        self.lbl_brand = QLabel("🌊 WaterMetrics")
        self.lbl_brand.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.lbl_brand.setStyleSheet("color: #028090;")

        self.btn_toggle = QPushButton("☰")
        self.btn_toggle.setObjectName("SecondaryButton")
        self.btn_toggle.setFixedSize(36, 36)
        self.btn_toggle.setToolTip("Focus Mode (Свернуть/Развернуть)")
        self.btn_toggle.clicked.connect(self.toggle_sidebar)

        header_layout.addWidget(self.lbl_brand)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_toggle)

        layout.addLayout(header_layout)

        # Кнопки навигации
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
        end_w = self.collapsed_width if not self.is_collapsed else self.expanded_width

        self.anim = QPropertyAnimation(self, b"minimumWidth")
        self.anim.setDuration(250)
        self.anim.setStartValue(start_w)
        self.anim.setEndValue(end_w)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        self.anim_max = QPropertyAnimation(self, b"maximumWidth")
        self.anim_max.setDuration(250)
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


# ==============================================================================
# PAGE 1: DASHBOARD (ОСНОВНАЯ ПАНЕЛЬ)
# ==============================================================================
class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("🛠 Основная панель расчетов")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # 1. Карточка выбора файлов
        card_files = QFrame()
        card_files.setObjectName("GlassCard")
        apply_oceanic_shadow(card_files)

        grid_f = QGridLayout(card_files)
        grid_f.setContentsMargins(18, 18, 18, 18)
        grid_f.setSpacing(12)
        grid_f.setColumnStretch(1, 1)

        # Файл шаблона
        grid_f.addWidget(QLabel("Шаблон (.xlsx):", objectName="FieldLabel"), 0, 0)
        self.txt_template = QLineEdit(placeholderText="Выберите файл прошлого месяца...")
        grid_f.addWidget(self.txt_template, 0, 1)
        btn_tpl = QPushButton("Обзор", objectName="SecondaryButton")
        btn_tpl.setFixedWidth(90)
        grid_f.addWidget(btn_tpl, 0, 2)
        self.lbl_tpl_stat = QLabel("⚪")
        grid_f.addWidget(self.lbl_tpl_stat, 0, 3)

        # Файл Аркус
        grid_f.addWidget(QLabel("Аркус (.xlsx):", objectName="FieldLabel"), 1, 0)
        self.txt_arcus = QLineEdit(placeholderText="Выберите файл текущего месяца...")
        grid_f.addWidget(self.txt_arcus, 1, 1)
        btn_arc = QPushButton("Обзор", objectName="SecondaryButton")
        btn_arc.setFixedWidth(90)
        grid_f.addWidget(btn_arc, 1, 2)
        self.lbl_arc_stat = QLabel("⚪")
        grid_f.addWidget(self.lbl_arc_stat, 1, 3)

        # Файл сохранения
        grid_f.addWidget(QLabel("Сохранить в:", objectName="FieldLabel"), 2, 0)
        self.txt_save = QLineEdit(placeholderText="Путь сохранения результата...")
        grid_f.addWidget(self.txt_save, 2, 1)
        btn_sav = QPushButton("Обзор", objectName="SecondaryButton")
        btn_sav.setFixedWidth(90)
        grid_f.addWidget(btn_sav, 2, 2)
        self.lbl_sav_stat = QLabel("⚪")
        grid_f.addWidget(self.lbl_sav_stat, 2, 3)

        # Мастер замен
        btn_repl = QPushButton("🔄 Замена счетчиков (Мастер)", objectName="AccentButton")
        btn_repl.setFixedHeight(38)
        grid_f.addWidget(btn_repl, 3, 0, 1, 4)

        layout.addWidget(card_files)

        # 2. Карточка числовых параметров
        card_targets = QFrame()
        card_targets.setObjectName("GlassCard")
        apply_oceanic_shadow(card_targets)

        grid_t = QGridLayout(card_targets)
        grid_t.setContentsMargins(18, 18, 18, 18)
        grid_t.setSpacing(12)
        grid_t.setColumnStretch(1, 1)
        grid_t.setColumnStretch(3, 1)

        grid_t.addWidget(QLabel("Цель ХВС (м³):", objectName="FieldLabel"), 0, 0)
        self.txt_cold = QLineEdit("0.0")
        grid_t.addWidget(self.txt_cold, 0, 1)

        grid_t.addWidget(QLabel("Цель ГВС (м³):", objectName="FieldLabel"), 0, 2)
        self.txt_hot = QLineEdit("0.0")
        grid_t.addWidget(self.txt_hot, 0, 3)

        grid_t.addWidget(QLabel("Коррекция ХВС:", objectName="FieldLabel"), 1, 0)
        self.txt_corr = QLineEdit("0")
        grid_t.addWidget(self.txt_corr, 1, 1)

        layout.addWidget(card_targets)

        # 3. Карточка истории файлов
        card_hist = QFrame()
        card_hist.setObjectName("GlassCard")
        apply_oceanic_shadow(card_hist)

        layout_h = QVBoxLayout(card_hist)
        layout_h.setContentsMargins(18, 18, 18, 18)
        layout_h.setSpacing(10)

        lbl_hist = QLabel("История созданных файлов", objectName="SectionTitle")
        layout_h.addWidget(lbl_hist)

        self.table_hist = QTableWidget(0, 2)
        self.table_hist.setHorizontalHeaderLabels(["Имя файла", "Полный путь"])
        self.table_hist.horizontalHeader().setFixedHeight(32)
        self.table_hist.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table_hist.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout_h.addWidget(self.table_hist)

        layout_btns = QHBoxLayout()
        layout_btns.setSpacing(10)

        btn_open = QPushButton("📂 Открыть файл", objectName="SecondaryButton")
        btn_rem = QPushButton("🗑 Удалить", objectName="DangerButton")
        btn_clr = QPushButton("🧹 Очистить", objectName="SecondaryButton")

        layout_btns.addWidget(btn_open)
        layout_btns.addWidget(btn_rem)
        layout_btns.addWidget(btn_clr)

        layout_h.addLayout(layout_btns)
        layout.addWidget(card_hist, 1)

        # Главная CTA Кнопка
        self.btn_run = QPushButton("🚀 Сформировать файл", objectName="PrimaryButton")
        self.btn_run.setFixedHeight(48)
        apply_oceanic_shadow(self.btn_run, blur=15, offset_y=4, alpha=35)
        layout.addWidget(self.btn_run)


# ==============================================================================
# PAGE 2: NORMS (НОРМАТИВЫ)
# ==============================================================================
class NormsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("📐 Настройка нормативов водопотребления")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("GlassCard")
        apply_oceanic_shadow(card)

        grid = QGridLayout(card)
        grid.setContentsMargins(22, 22, 22, 22)
        grid.setSpacing(16)
        grid.setColumnStretch(1, 1)

        desc = QLabel(
            "Нормативы используются при распределении объемов воды для лицевых счетов,\n"
            "начисляющих плату по нормативу при отсутствии показаний приборов учета."
        )
        desc.setStyleSheet("color: #475569; font-size: 13px; line-height: 1.4;")
        grid.addWidget(desc, 0, 0, 1, 2)

        grid.addWidget(QLabel("Норматив ХВС (м³ на чел.):", objectName="FieldLabel"), 1, 0)
        self.txt_norm_cold = QLineEdit("4.04")
        self.txt_norm_cold.setMaximumWidth(200)
        grid.addWidget(self.txt_norm_cold, 1, 1)

        grid.addWidget(QLabel("Норматив ГВС (м³ на чел.):", objectName="FieldLabel"), 2, 0)
        self.txt_norm_hot = QLineEdit("2.65")
        self.txt_norm_hot.setMaximumWidth(200)
        grid.addWidget(self.txt_norm_hot, 2, 1)

        btn_save_norms = QPushButton("💾 Сохранить нормативы", objectName="PrimaryButton")
        btn_save_norms.setFixedWidth(220)
        grid.addWidget(btn_save_norms, 3, 0, 1, 2)

        layout.addWidget(card)
        layout.addStretch()


# ==============================================================================
# PAGE 3: LOGS (ТЕРМИНАЛ ЛОГОВ)
# ==============================================================================
class LogsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("📋 Терминал системных логов")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("GlassCard")
        apply_oceanic_shadow(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)

        # Фильтры
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(16)

        self.chk_info = QCheckBox("INFO")
        self.chk_info.setChecked(True)
        self.chk_success = QCheckBox("SUCCESS")
        self.chk_success.setChecked(True)
        self.chk_error = QCheckBox("ERROR")
        self.chk_error.setChecked(True)

        btn_clear_log = QPushButton("🧹 Очистить консоль", objectName="SecondaryButton")

        filter_layout.addWidget(self.chk_info)
        filter_layout.addWidget(self.chk_success)
        filter_layout.addWidget(self.chk_error)
        filter_layout.addStretch()
        filter_layout.addWidget(btn_clear_log)

        card_layout.addLayout(filter_layout)

        # Окно консоли
        self.log_viewer = QTextEdit()
        self.log_viewer.setObjectName("LogViewer")
        self.log_viewer.setReadOnly(True)
        self.log_viewer.append('<span style="color: #0077B6;"><b>[INFO]</b> Система WaterMetrics инициализирована.</span>')
        self.log_viewer.append('<span style="color: #10B981;"><b>[SUCCESS]</b> Графическая оболочка Oceanic Glass подгружена.</span>')

        card_layout.addWidget(self.log_viewer, 1)
        layout.addWidget(card, 1)


# ==============================================================================
# PAGE 4: AUTO-TESTS (АВТО-ТЕСТЫ)
# ==============================================================================
class AutoTestsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("🧪 Автоматическое тестирование алгоритмов")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("GlassCard")
        apply_oceanic_shadow(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)

        ctrl_layout = QHBoxLayout()
        btn_run = QPushButton("▶ Запустить Тест (+100m³ / -100m³)", objectName="PrimaryButton")
        btn_del = QPushButton("🗑 Удалить результаты", objectName="DangerButton")
        btn_folder = QPushButton("📁 Открыть папку с тестами", objectName="SecondaryButton")

        ctrl_layout.addWidget(btn_run)
        ctrl_layout.addWidget(btn_del)
        ctrl_layout.addWidget(btn_folder)
        ctrl_layout.addStretch()

        card_layout.addLayout(ctrl_layout)

        self.test_log = QTextEdit()
        self.test_log.setObjectName("LogViewer")
        self.test_log.setReadOnly(True)
        self.test_log.append('<span style="color: #0077B6;"><b>[TEST]</b> Готов к запуску автоматического сценария...</span>')

        card_layout.addWidget(self.test_log, 1)
        layout.addWidget(card, 1)


# ==============================================================================
# PAGE 5: ABOUT (О ПРОГРАММЕ)
# ==============================================================================
class AboutPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("ℹ️ О программе")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        card = QFrame()
        card.setObjectName("GlassCard")
        apply_oceanic_shadow(card)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(14)

        appName = QLabel("WaterMetrics Professional Edition")
        appName.setStyleSheet("font-size: 24px; font-weight: bold; color: #028090;")

        sub = QLabel("Система автоматизированного расчета и распределения объемов водопотребления")
        sub.setStyleSheet("font-size: 14px; color: #475569;")

        ver = QLabel("Версия: 2.0 (PySide6 Oceanic Glass Edition)")
        ver.setStyleSheet("font-size: 12px; color: #94A3B8; font-weight: 600;")

        btns = QHBoxLayout()
        btns.setSpacing(12)

        btn_donate = QPushButton("💳 Пожертвования", objectName="SecondaryButton")
        btn_beach = QPushButton("🏖 Морской Отдых", objectName="AccentButton")

        btns.addWidget(btn_donate)
        btns.addWidget(btn_beach)

        card_layout.addWidget(appName, alignment=Qt.AlignCenter)
        card_layout.addWidget(sub, alignment=Qt.AlignCenter)
        card_layout.addWidget(ver, alignment=Qt.AlignCenter)
        card_layout.addSpacing(10)
        card_layout.addLayout(btns)
        card_layout.addStretch()

        layout.addWidget(card, 1)


# ==============================================================================
# MAIN APPLICATION SHELL (QMainWindow + QSplitter)
# ==============================================================================
class MainWindowShell(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WaterMetrics — Oceanic Glass Premium Edition")
        self.setMinimumSize(1050, 700)

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget(self)
        central_widget.setObjectName("MainContainer")
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # QSplitter для гибкой регулировки пропорций мышью
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(1)

        # Левый сворачиваемый Sidebar
        self.sidebar = CollapsibleSidebar()
        self.splitter.addWidget(self.sidebar)

        # Правый стек страниц
        self.stacked_widget = QStackedWidget()

        self.page_dashboard = DashboardPage()
        self.page_norms = NormsPage()
        self.page_logs = LogsPage()
        self.page_tests = AutoTestsPage()
        self.page_about = AboutPage()

        self.stacked_widget.addWidget(self.page_dashboard)
        self.stacked_widget.addWidget(self.page_norms)
        self.stacked_widget.addWidget(self.page_logs)
        self.stacked_widget.addWidget(self.page_tests)
        self.stacked_widget.addWidget(self.page_about)

        # Область прокрутки правого контента
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("background: transparent;")
        scroll_area.setWidget(self.stacked_widget)

        self.splitter.addWidget(scroll_area)

        # Приоритет растяжения: 0 для Sidebar, 1 для правого контента
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        root_layout.addWidget(self.splitter)

        # Нижная строка состояния (StatusBar)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Готов к работе")
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(180)
        self.progress_bar.setVisible(False)

        self.status_bar.addWidget(self.status_label)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # Привязка кнопок навигации
        for btn in self.sidebar.nav_buttons:
            btn.clicked.connect(self._on_nav_button_clicked)

        # Выбираем первую страницу по умолчанию
        if self.sidebar.nav_buttons:
            self.sidebar.nav_buttons[0].setChecked(True)

    def _on_nav_button_clicked(self):
        sender = self.sender()
        if sender:
            idx = sender.property("pageIndex")
            self.stacked_widget.setCurrentIndex(idx)

            for btn in self.sidebar.nav_buttons:
                btn.setChecked(btn == sender)


# ==============================================================================
# MAIN EXECUTION ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(OCEANIC_GLASS_QSS)

    window = MainWindowShell()
    window.show()

    sys.exit(app.exec())