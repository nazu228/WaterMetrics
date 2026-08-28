from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QSize, Signal
from ui.styles import get_svg_icon, ThemeManager
from ui.components.interactive import HoverGlassCard
from ui.components.glass_icon import GlassIconWidget
from ui.components.toast import ToastNotification
from services.settings_service import SettingsService


class NormsPage(QWidget):
    """Страница редактирования нормативов с персистентным сохранением и справкой."""

    norms_changed = Signal(float, float)

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

        # Загрузка актуальных нормативов из SettingsService
        saved_cold, saved_hot = SettingsService.get_norms()

        grid.addWidget(QLabel("Норматив ХВС (м³/чел):", objectName="FieldLabel"), 2, 0)
        self.txt_norm_cold = QLineEdit(str(saved_cold))
        self.txt_norm_cold.setMaximumWidth(140)
        self.txt_norm_cold.setMinimumHeight(36)
        self.txt_norm_cold.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px 8px;")
        self.txt_norm_cold.setPlaceholderText("4.04")
        grid.addWidget(self.txt_norm_cold, 2, 1)

        grid.addWidget(QLabel("Норматив ГВС (м³/чел):", objectName="FieldLabel"), 3, 0)
        self.txt_norm_hot = QLineEdit(str(saved_hot))
        self.txt_norm_hot.setMaximumWidth(140)
        self.txt_norm_hot.setMinimumHeight(36)
        self.txt_norm_hot.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px 8px;")
        self.txt_norm_hot.setPlaceholderText("2.65")
        grid.addWidget(self.txt_norm_hot, 3, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_save = QPushButton("  Сохранить", objectName="PrimaryButton")
        btn_save.setIcon(get_svg_icon("save", color="#020617"))
        btn_save.setMinimumHeight(38)
        btn_save.setStyleSheet("font-size: 13.5px; font-weight: 800;")
        btn_save.clicked.connect(self._save_norms)
        btn_row.addWidget(btn_save, 2)

        btn_reset = QPushButton("Сброс", objectName="SecondaryButton")
        btn_reset.setMinimumHeight(38)
        btn_reset.setStyleSheet("font-size: 13px; font-weight: 600;")
        btn_reset.setToolTip("Сбросить к заводским нормативам (ХВС: 4.04, ГВС: 2.65)")
        btn_reset.clicked.connect(self._reset_norms)
        btn_row.addWidget(btn_reset, 1)

        grid.addLayout(btn_row, 4, 0, 1, 2)

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
            b_lay.setContentsMargins(10, 8, 10, 8)
            b_lay.setSpacing(4)

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
        # Синхронизация полей ввода с актуальными сохраненными значениями
        saved_cold, saved_hot = SettingsService.get_norms()
        self.txt_norm_cold.setText(str(saved_cold))
        self.txt_norm_hot.setText(str(saved_hot))
        self._update_theme_styles()

    def _update_theme_styles(self, theme_name: str = None):
        curr_theme = theme_name or ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")
        accent = ThemeManager.get_current_accent_color()

        head_color = ("#0A246A" if curr_theme == "Как дома" else "#028090") if is_light else accent
        sub_color = "#334155" if is_light else "#E2E8F0"
        box_bg = "rgba(10, 36, 106, 0.04)" if curr_theme == "Как дома" else ("rgba(2, 128, 144, 0.06)" if curr_theme == "Pearl Light" else "rgba(255, 255, 255, 0.04)")
        box_border = "#7F9DB9" if curr_theme == "Как дома" else ("rgba(2, 128, 144, 0.25)" if curr_theme == "Pearl Light" else "rgba(255, 255, 255, 0.12)")

        if hasattr(self, 'desc_label'):
            self.desc_label.setStyleSheet(f"color: {sub_color}; font-size: 13.5px; line-height: 1.45;")

        if hasattr(self, 'law_widgets'):
            for box, lh, lt in self.law_widgets:
                box.setStyleSheet(f"background: {box_bg}; border: 1.5px solid {box_border}; border-radius: 8px; padding: 8px 12px;")
                lh.setStyleSheet(f"color: {head_color}; font-weight: bold; font-size: 13.5px;")
                lt.setStyleSheet(f"color: {sub_color}; font-size: 13px; line-height: 1.4;")

    def _save_norms(self):
        try:
            val_c = float(self.txt_norm_cold.text().strip().replace(',', '.'))
            val_h = float(self.txt_norm_hot.text().strip().replace(',', '.'))
            if val_c <= 0 or val_h <= 0:
                raise ValueError("Значения должны быть строго больше нуля")
        except ValueError:
            ToastNotification.show_toast(self.window(), "Введите корректные положительные числа!", "ERROR")
            return

        success = SettingsService.save_norms(val_c, val_h)
        if success:
            self.txt_norm_cold.setText(str(val_c))
            self.txt_norm_hot.setText(str(val_h))
            self.norms_changed.emit(val_c, val_h)
            ToastNotification.show_toast(
                self.window(),
                f"Нормативы сохранены: ХВС = {val_c} м³, ГВС = {val_h} м³",
                "SUCCESS"
            )
        else:
            ToastNotification.show_toast(self.window(), "Не удалось сохранить нормативы", "ERROR")

    def _reset_norms(self):
        def_c, def_h = SettingsService.reset_norms_to_default()
        self.txt_norm_cold.setText(str(def_c))
        self.txt_norm_hot.setText(str(def_h))
        self.norms_changed.emit(def_c, def_h)
        ToastNotification.show_toast(
            self.window(),
            f"Нормативы сброшены: ХВС = {def_c} м³, ГВС = {def_h} м³",
            "INFO"
        )