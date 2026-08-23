"""
Командная палитра WaterMetrics (Command Palette Overlay - Ctrl+K / Ctrl+P).
Мгновенный поиск и выполнение команд приложения.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QLabel, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QKeyEvent
from ui.styles import ThemeManager, get_svg_icon


class CommandPaletteDialog(QDialog):
    """Модальная командная палитра с фильтрацией в реальном времени."""

    def __init__(self, parent=None, actions=None):
        super().__init__(parent)
        self.setWindowTitle("Командная палитра WaterMetrics")
        self.setFixedSize(540, 360)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        if not actions:
            if parent and hasattr(parent, 'run_calculation'):
                actions = [
                    ("Запустить расчет водопотребления (Ctrl+R / F5)", "run", parent.run_calculation),
                    ("Переключить в Режим Аркуса (Classic)", "dashboard", getattr(parent, '_toggle_arcus_mode', None)),
                    ("Открыть терминал логов (Ctrl+L)", "logs", lambda: parent.switch_page(2)),
                    ("Настроить 3D-волны и оформление", "about", lambda: parent.switch_page(4)),
                    ("Мастер замен счетчиков ИПУ", "replace", getattr(parent, 'open_replacement_dialog', None)),
                    ("Загрузить файл шаблона (Ctrl+O)", "folder", getattr(getattr(parent, 'page_main', None), 'drop_tpl', None).open_file_dialog if hasattr(getattr(parent, 'page_main', None), 'drop_tpl') else None),
                    ("Загрузить файл Аркуса", "folder", getattr(getattr(parent, 'page_main', None), 'drop_arc', None).open_file_dialog if hasattr(getattr(parent, 'page_main', None), 'drop_arc') else None),
                    ("Следующая тема оформления", "dashboard", getattr(parent, '_cycle_theme', None)),
                    ("Сбросить сетку конструктора", "toggle", getattr(getattr(parent, 'page_main', None), '_reset_grid', None))
                ]
            else:
                actions = [
                    ("Запустить расчет водопотребления (Ctrl+R / F5)", "run", None),
                    ("Переключить в Режим Аркуса (Classic)", "dashboard", None),
                    ("Открыть терминал логов (Ctrl+L)", "logs", None),
                    ("Настроить 3D-волны и оформление", "about", None),
                    ("Мастер замен счетчиков ИПУ", "replace", None),
                    ("Загрузить файл шаблона (Ctrl+O)", "folder", None),
                    ("Загрузить файл Аркуса", "folder", None),
                    ("Следующая тема оформления", "dashboard", None),
                    ("Сбросить сетку конструктора", "toggle", None)
                ]

        self.actions = actions
        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        accent = ThemeManager.get_current_accent_color()

        if curr_theme == "Как дома":
            card_bg = "#ECE9D8"
            card_border = "#7F9DB9"
            card_radius = "4px"
            input_bg = "#FFFFFF"
            input_border = "#7F9DB9"
            input_color = "#000000"
            item_color = "#000000"
            item_sel_bg = "#0A246A"
            item_sel_color = "#FFFFFF"
            hint_color = "#444444"
        elif curr_theme == "Pearl Light":
            card_bg = "rgba(248, 250, 252, 0.98)"
            card_border = "#028090"
            card_radius = "16px"
            input_bg = "#FFFFFF"
            input_border = "#CBD5E1"
            input_color = "#0F172A"
            item_color = "#0F172A"
            item_sel_bg = "rgba(2, 128, 144, 0.18)"
            item_sel_color = "#028090"
            hint_color = "#475569"
        else:
            card_bg = "rgba(15, 23, 42, 0.95)"
            card_border = accent
            card_radius = "16px"
            input_bg = "rgba(30, 41, 59, 0.8)"
            input_border = accent
            input_color = "#F8FAFC"
            item_color = "#F8FAFC"
            item_sel_bg = "rgba(0, 242, 254, 0.18)"
            item_sel_color = accent
            hint_color = "#94A3B8"

        self.card = QFrame()
        self.card.setObjectName("GlassCard")
        self.card.setStyleSheet(f"""
            QFrame#GlassCard {{
                background-color: {card_bg};
                border: 2px solid {card_border};
                border-radius: {card_radius};
            }}
        """)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(14, 14, 14, 14)
        card_layout.setSpacing(10)

        # Строка поиска
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Введите команду или действие (например: Расчет, Тема, Логи)...")
        self.search_edit.setMinimumHeight(40)
        self.search_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {input_bg};
                border: 1px solid {input_border};
                border-radius: 10px;
                padding: 8px 14px;
                font-size: 14px;
                color: {input_color};
            }}
        """)
        self.search_edit.textChanged.connect(self._filter_actions)
        card_layout.addWidget(self.search_edit)

        # Список команд
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                padding: 10px 14px;
                border-radius: 8px;
                color: {item_color};
                font-size: 13px;
                font-weight: 600;
            }}
            QListWidget::item:selected, QListWidget::item:hover {{
                background-color: {item_sel_bg};
                color: {item_sel_color};
            }}
            QScrollBar:vertical {{
                background: rgba(255, 255, 255, 0.04);
                width: 6px;
                border-radius: 3px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.20);
                border-radius: 3px;
                min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {accent};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; background: transparent; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)
        self.list_widget.itemActivated.connect(self._execute_selected)
        card_layout.addWidget(self.list_widget, 1)

        hint = QLabel("💡 Навигация: ↑↓ для выбора, Enter — выполнить, Esc — закрыть")
        hint.setStyleSheet(f"color: {hint_color}; font-size: 11px; font-weight: 500;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(hint)

        root_layout.addWidget(self.card)
        self._populate_list()

    def _populate_list(self):
        curr_theme = ThemeManager.get_current_theme_name()
        accent = ThemeManager.get_current_accent_color()
        icon_color = "#0A246A" if curr_theme == "Как дома" else ("#028090" if curr_theme == "Pearl Light" else accent)

        self.list_widget.clear()
        for title, icon_key, callback in self.actions:
            clean_title = title
            for emo in ("⚡ ", "🏛️ ", "📜 ", "🌊 ", "🔧 ", "📁 ", "🎨 ", "📊 "):
                if clean_title.startswith(emo):
                    clean_title = clean_title[len(emo):]

            item = QListWidgetItem(f"  {clean_title}")
            item.setIcon(get_svg_icon(icon_key if icon_key else "dashboard", color=icon_color))
            item.setData(Qt.ItemDataRole.UserRole, callback)
            self.list_widget.addItem(item)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _filter_actions(self, text: str):
        query = text.strip().lower()
        first_visible = -1
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            matches = not query or (query in item.text().lower())
            item.setHidden(not matches)
            if matches and first_visible == -1:
                first_visible = i

        if first_visible != -1:
            self.list_widget.setCurrentRow(first_visible)

    def showEvent(self, event):
        super().showEvent(event)
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def _execute_selected(self, item=None):
        if item is None:
            item = self.list_widget.currentItem()
        if item and not item.isHidden():
            callback = item.data(Qt.ItemDataRole.UserRole)
            self.accept()
            if callable(callback):
                callback()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Down:
            curr = self.list_widget.currentRow()
            if curr < self.list_widget.count() - 1:
                self.list_widget.setCurrentRow(curr + 1)
            return
        elif event.key() == Qt.Key.Key_Up:
            curr = self.list_widget.currentRow()
            if curr > 0:
                self.list_widget.setCurrentRow(curr - 1)
            return
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._execute_selected()
            return
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)
