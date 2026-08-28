from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QCheckBox, QFrame, QLineEdit, QFileDialog
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QTextCursor
from ui.styles import get_svg_icon, ThemeManager
from ui.components.interactive import HoverGlassCard
from ui.components.toast import ToastNotification


class LogsPage(QWidget):
    """Страница системных логов с поиском, экспортом в файл и автоскроллом."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LogsPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.raw_logs = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Терминал системных логов", objectName="PageTitle")
        title.setWordWrap(False)
        layout.addWidget(title)

        card = HoverGlassCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)

        # Фильтры и поиск
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск по логам...")
        self.search_edit.setMinimumHeight(34)
        self.search_edit.setStyleSheet("font-size: 13.5px;")
        self.search_edit.textChanged.connect(self._filter_logs_display)

        self.chk_info = QCheckBox("INFO")
        self.chk_info.setStyleSheet("font-size: 13px; font-weight: bold;")
        self.chk_info.setChecked(True)
        self.chk_info.toggled.connect(self._filter_logs_display)

        self.chk_success = QCheckBox("SUCCESS")
        self.chk_success.setStyleSheet("font-size: 13px; font-weight: bold;")
        self.chk_success.setChecked(True)
        self.chk_success.toggled.connect(self._filter_logs_display)

        self.chk_error = QCheckBox("ERROR")
        self.chk_error.setStyleSheet("font-size: 13px; font-weight: bold;")
        self.chk_error.setChecked(True)
        self.chk_error.toggled.connect(self._filter_logs_display)

        btn_export_log = QPushButton("Экспорт в файл", objectName="SecondaryButton")
        btn_export_log.setIcon(get_svg_icon("save"))
        btn_export_log.setMinimumHeight(34)
        btn_export_log.setStyleSheet("font-size: 13px; font-weight: 600;")
        btn_export_log.clicked.connect(self._export_logs)

        btn_clear_log = QPushButton("Очистить", objectName="SecondaryButton")
        btn_clear_log.setIcon(get_svg_icon("trash"))
        btn_clear_log.setMinimumHeight(34)
        btn_clear_log.setStyleSheet("font-size: 13px; font-weight: 600;")
        btn_clear_log.clicked.connect(self._clear_logs)

        filter_layout.addWidget(self.search_edit, 1)
        filter_layout.addWidget(self.chk_info)
        filter_layout.addWidget(self.chk_success)
        filter_layout.addWidget(self.chk_error)
        filter_layout.addWidget(btn_export_log)
        filter_layout.addWidget(btn_clear_log)

        card_layout.addLayout(filter_layout)

        # Консоль
        self.log_viewer = QTextEdit()
        self.log_viewer.setObjectName("LogViewer")
        self.log_viewer.setStyleSheet("font-family: 'Consolas', 'JetBrains Mono', monospace; font-size: 13px; line-height: 1.4;")
        self.log_viewer.setReadOnly(True)
        self.log_viewer.document().setMaximumBlockCount(5000)

        self.append_log("Система WaterMetrics инициализирована.", "INFO")
        self.append_log("Графический интерфейс Apple Frosted Glass загружен.", "SUCCESS")

        card_layout.addWidget(self.log_viewer, 1)
        layout.addWidget(card, 1)

        ThemeManager.on_theme_changed.append(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str = None):
        self._filter_logs_display()

    def _get_level_color(self, level: str) -> str:
        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        lvl = level.upper()
        if is_light:
            if lvl == "SUCCESS":
                return "#15803D"
            elif lvl == "ERROR":
                return "#DC2626"
            elif lvl == "WARNING":
                return "#B45309"
            else:
                return "#0A246A" if curr_theme == "Как дома" else "#0369A1"
        else:
            accent = ThemeManager.get_current_accent_color()
            if lvl == "SUCCESS":
                return "#10B981"
            elif lvl == "ERROR":
                return "#F87171"
            elif lvl == "WARNING":
                return "#FBBF24"
            else:
                return accent

    @Slot(str, str)
    def append_log(self, message: str, level: str = "INFO"):
        """Добавление лога с автопрокруткой вниз и сохранением истории."""
        clean_msg = message.strip()
        for prefix in ("[INFO]", "[SUCCESS]", "[ERROR]", "[WARNING]"):
            if clean_msg.upper().startswith(prefix):
                clean_msg = clean_msg[len(prefix):].strip()

        self.raw_logs.append((clean_msg, level.upper()))

        if level.upper() == "INFO" and not self.chk_info.isChecked():
            return
        if level.upper() == "SUCCESS" and not self.chk_success.isChecked():
            return
        if level.upper() == "ERROR" and not self.chk_error.isChecked():
            return

        query = self.search_edit.text().strip().lower()
        if query and query not in clean_msg.lower():
            return

        color = self._get_level_color(level)
        self.log_viewer.append(f'<span style="color: {color};"><b>[{level.upper()}]</b> {clean_msg}</span>')
        self.log_viewer.moveCursor(QTextCursor.MoveOperation.End)

    def _filter_logs_display(self):
        self.log_viewer.clear()
        query = self.search_edit.text().strip().lower()

        for msg, lvl in self.raw_logs:
            if lvl == "INFO" and not self.chk_info.isChecked():
                continue
            if lvl == "SUCCESS" and not self.chk_success.isChecked():
                continue
            if lvl == "ERROR" and not self.chk_error.isChecked():
                continue

            if query and query not in msg.lower():
                continue

            color = self._get_level_color(lvl)
            self.log_viewer.append(f'<span style="color: {color};"><b>[{lvl}]</b> {msg}</span>')

        self.log_viewer.moveCursor(QTextCursor.MoveOperation.End)

    def _export_logs(self):
        if not self.raw_logs:
            ToastNotification.show_toast(self, "Логи пусты!", "INFO")
            return
        save_path, _ = QFileDialog.getSaveFileName(self, "Экспорт системных логов", "WaterMetrics_Logs.txt", "Text Files (*.txt *.log)")
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    for msg, lvl in self.raw_logs:
                        f.write(f"[{lvl}] {msg}\n")
                ToastNotification.show_toast(self, "Логи успешно сохранены в файл!", "SUCCESS")
            except Exception as e:
                ToastNotification.show_toast(self, f"Ошибка сохранения логов: {e}", "ERROR")

    def _clear_logs(self):
        self.raw_logs.clear()
        self.log_viewer.clear()
        ToastNotification.show_toast(self, "Консоль логов очищена", "INFO")