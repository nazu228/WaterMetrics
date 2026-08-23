from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QSize
from ui.styles import get_svg_icon, ThemeManager
from ui.components.interactive import HoverGlassCard
from ui.components.glass_icon import GlassIconWidget
from ui.components.toast import ToastNotification


class NormsPage(QWidget):
    """Страница редактирования нормативов с двухколоночным макетом и справкой."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NormsPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Настройка нормативов водопотребления", objectName="PageTitle")
        title.setWordWrap(False)
        layout.addWidget(title)

        content_row = QHBoxLayout()
        content_row.setSpacing(16)

        # ─── Левая колонка: Форма редактирования ───
        card_form = HoverGlassCard()
        card_form.setMinimumWidth(320)
        card_form.setMaximumWidth(420)
        grid = QGridLayout(card_form)
        grid.setContentsMargins(20, 20, 20, 20)
        grid.setSpacing(14)
        grid.setColumnStretch(1, 1)

        lbl_form_title = QLabel("Параметры начисления", objectName="SectionTitle")
        grid.addWidget(lbl_form_title, 0, 0, 1, 2)

        self.desc_label = QLabel(
            "Нормативы применяются при распределении объемов для лицевых счетов "
            "без приборов учета или при непредоставлении показаний."
        )
        self.desc_label.setWordWrap(True)
        grid.addWidget(self.desc_label, 1, 0, 1, 2)

        grid.addWidget(QLabel("Норматив ХВС (м³/чел):", objectName="FieldLabel"), 2, 0)
        self.txt_norm_cold = QLineEdit("4.04")
        self.txt_norm_cold.setMaximumWidth(140)
        grid.addWidget(self.txt_norm_cold, 2, 1)

        grid.addWidget(QLabel("Норматив ГВС (м³/чел):", objectName="FieldLabel"), 3, 0)
        self.txt_norm_hot = QLineEdit("2.65")
        self.txt_norm_hot.setMaximumWidth(140)
        grid.addWidget(self.txt_norm_hot, 3, 1)

        btn_save = QPushButton("  Сохранить нормативы", objectName="PrimaryButton")
        btn_save.setIcon(get_svg_icon("save", color="#020617"))
        btn_save.setMinimumHeight(36)
        btn_save.clicked.connect(self._save_norms)
        grid.addWidget(btn_save, 4, 0, 1, 2)

        content_row.addWidget(card_form)

        # ─── Правая колонка: Информационная карточка по алгоритмам ───
        card_info = HoverGlassCard()
        info_lay = QVBoxLayout(card_info)
        info_lay.setContentsMargins(22, 20, 22, 20)
        info_lay.setSpacing(12)

        lbl_info_title = QLabel("📖 Справка по алгоритмам распределения", objectName="SectionTitle")
        info_lay.addWidget(lbl_info_title)

        laws = [
            ("1. По показаниям ИПУ (Закон 1)", "Прямой расход: V = Текущее_показание - Предыдущее_показание."),
            ("2. По среднемесячному расходу (Закон 2)", "При отсутствии показаний до 3 месяцев: расчет по среднему объему помещения."),
            ("3. По нормативу потребления (Закон 3)", "При отсутствии ИПУ или показаний > 3 мес: V = Проживающих × Норматив."),
            ("4. Распределение небаланса (ОДН)", "Разница между общедомовым вводом и суммой квартир пропорционально распределяется по лицевым счетам.")
        ]

        self.law_widgets = []
        for head_str, text_str in laws:
            box = QFrame()
            b_lay = QVBoxLayout(box)
            b_lay.setContentsMargins(8, 6, 8, 6)
            b_lay.setSpacing(2)

            lh = QLabel(head_str)
            lt = QLabel(text_str)
            lt.setWordWrap(True)

            b_lay.addWidget(lh)
            b_lay.addWidget(lt)
            info_lay.addWidget(box)
            self.law_widgets.append((box, lh, lt))

        info_lay.addStretch()
        content_row.addWidget(card_info, 1)

        layout.addLayout(content_row)
        layout.addStretch()

        ThemeManager.on_theme_changed.append(self._update_theme_styles)
        self._update_theme_styles()

    def showEvent(self, event):
        super().showEvent(event)
        self._update_theme_styles()

    def _update_theme_styles(self, theme_name: str = None):
        curr_theme = theme_name or ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        accent = ThemeManager.get_current_accent_color()

        head_color = ("#0A246A" if curr_theme == "Как дома" else "#028090") if is_light else accent
        sub_color = "#475569" if is_light else "#94A3B8"
        box_bg = "rgba(10, 36, 106, 0.04)" if curr_theme == "Как дома" else ("rgba(2, 128, 144, 0.06)" if curr_theme == "Pearl Light" else "rgba(255, 255, 255, 0.03)")
        box_border = "#7F9DB9" if curr_theme == "Как дома" else ("rgba(2, 128, 144, 0.25)" if curr_theme == "Pearl Light" else "rgba(255, 255, 255, 0.08)")

        if hasattr(self, 'desc_label'):
            self.desc_label.setStyleSheet(f"color: {sub_color}; font-size: 12px; line-height: 1.4;")

        if hasattr(self, 'law_widgets'):
            for box, lh, lt in self.law_widgets:
                box.setStyleSheet(f"background: {box_bg}; border: 1px solid {box_border}; border-radius: 8px; padding: 6px 10px;")
                lh.setStyleSheet(f"color: {head_color}; font-weight: bold; font-size: 12px;")
                lt.setStyleSheet(f"color: {sub_color}; font-size: 11px;")

    def _save_norms(self):
        ToastNotification.show_toast(self.window(), "Нормативы успешно сохранены и обновлены", "SUCCESS")