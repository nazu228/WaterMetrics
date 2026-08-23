"""
Диалоговое окно Мастера замен счетчиков.
Содержит динамический поиск квартир, бейджи ХВС/ГВС, индикацию [✓ Замена],
возможность редактирования записей и кнопку полного сброса.
"""

import re
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QScrollArea, QWidget, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Slot
from models import ClosedMeterRecord, NewMeterRecord
from ui.styles import get_svg_icon, ThemeManager
from ui.components.toast import ToastNotification


def _get_apt_score(apt: str, query: str) -> int:
    """Приоритетная сортировка поиска квартир."""
    q = query.strip().lower()
    if not q:
        return 0
    apt_lower = apt.lower()

    if apt_lower == q or f"квартира {q}" == apt_lower:
        return 0

    if q.isdigit():
        m = re.search(r'\d+', apt_lower)
        if m:
            num_str = m.group(0)
            if num_str == q:
                return 0
            if num_str.startswith(q):
                return 1
            if q in num_str:
                return 2

    if apt_lower.startswith(q):
        return 1
    if q in apt_lower:
        return 3

    return 999


class MeterReplacementDialog(QDialog):
    """Мастер замен ИПУ с поиском и динамической фильтрацией."""

    def __init__(self, parent=None, apts_data=None, closed_meters=None, new_meters=None):
        super().__init__(parent)
        self.setWindowTitle("Мастер замен счетчиков ИПУ")
        self.resize(640, 560)
        self.apts_data = apts_data or {}

        self.closed_records = list(closed_meters or [])
        self.new_records = list(new_meters or [])

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        lbl_title = QLabel("Управление закрытыми и новыми ИПУ", objectName="PageTitle")
        layout.addWidget(lbl_title)

        form_card = QFrame()
        form_card.setObjectName("GlassCard")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(14, 14, 14, 14)
        form_layout.setSpacing(10)

        # 0. Поиск квартир с иконкой лупы и автоматической кнопкой очистки
        search_row = QHBoxLayout()
        lbl_search_icon = QLabel()
        lbl_search_icon.setPixmap(get_svg_icon("search").pixmap(18, 18))
        search_row.addWidget(lbl_search_icon)

        search_row.addWidget(QLabel("Поиск помещения:", objectName="FieldLabel"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Введите номер квартиры или название...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        search_row.addWidget(self.search_edit, 1)
        form_layout.addLayout(search_row)

        # 1. Выпадающий список квартир
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Квартира:", objectName="FieldLabel"))
        self.combo_apt = QComboBox()
        self.combo_apt.currentTextChanged.connect(self._update_meters_combo)
        row1.addWidget(self.combo_apt, 1)
        form_layout.addLayout(row1)

        # 2. Выбор прибора
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Прибор:", objectName="FieldLabel"))
        self.combo_meter = QComboBox()
        self.combo_meter.currentIndexChanged.connect(self._on_meter_selected)
        row2.addWidget(self.combo_meter, 1)
        form_layout.addLayout(row2)

        # 3. Показания
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Финальное (старый):", objectName="FieldLabel"))
        self.txt_final = QLineEdit("0.0")
        row3.addWidget(self.txt_final)

        row3.addWidget(QLabel("Начальное (новый):", objectName="FieldLabel"))
        self.txt_initial = QLineEdit("0.0")
        row3.addWidget(self.txt_initial)

        form_layout.addLayout(row3)

        btn_add = QPushButton("Добавить / Обновить замену", objectName="PrimaryButton")
        btn_add.setIcon(get_svg_icon("plus", color="#020617"))
        btn_add.clicked.connect(self._add_replacement)
        form_layout.addWidget(btn_add)

        layout.addWidget(form_card)

        # Заголовок списка с кнопкой Сброса Всех замен
        list_hdr_layout = QHBoxLayout()
        list_hdr_layout.addWidget(QLabel("Зафиксированные замены:", objectName="SectionTitle"))
        list_hdr_layout.addStretch()

        btn_reset_all = QPushButton("Сбросить все", objectName="DangerButton")
        btn_reset_all.setIcon(get_svg_icon("trash", color="#F87171"))
        btn_reset_all.clicked.connect(self._reset_all)
        list_hdr_layout.addWidget(btn_reset_all)

        layout.addLayout(list_hdr_layout)

        # Область списка
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.scroll_area.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent !important; border: none; }")

        self.scroll_content = QWidget()
        self.scroll_content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area, 1)

        # Кнопки
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Отмена", objectName="SecondaryButton")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Сохранить и применить", objectName="PrimaryButton")
        btn_save.setIcon(get_svg_icon("save", color="#020617"))
        btn_save.clicked.connect(self.accept)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

        self._populate_apartments()
        self._refresh_list_view()

    def _populate_apartments(self, query: str = ""):
        """Заполнение списка квартир с маркой [✓ Замена]."""
        self.combo_apt.blockSignals(True)
        self.combo_apt.clear()

        all_apts = list(self.apts_data.keys())
        scored = []

        for apt in all_apts:
            score = _get_apt_score(apt, query)
            if score < 999:
                scored.append((score, apt))

        def natural_key(item):
            s, name = item
            m = re.search(r'\d+', name)
            num = int(m.group(0)) if m else 999999
            return (s, num, name)

        scored.sort(key=natural_key)

        replaced_apts = {r.apartment for r in self.closed_records}

        for _, apt in scored:
            is_replaced = apt in replaced_apts
            disp = f"{apt} [✓ Замена]" if is_replaced else apt
            self.combo_apt.addItem(disp, userData=apt)

        self.combo_apt.blockSignals(False)
        self._update_meters_combo()

    @Slot(str)
    def _on_search_text_changed(self, text: str):
        self._populate_apartments(text)

    def _update_meters_combo(self):
        self.combo_meter.blockSignals(True)
        self.combo_meter.clear()
        apt = self.combo_apt.currentData() or self.combo_apt.currentText().replace(" [✓ Замена]", "")
        if apt and apt in self.apts_data:
            for m in self.apts_data[apt]:
                w_type = "ХВС" if m['type'] == 'cold' else "ГВС"
                prev_val = m.get('prev', 0.0)
                disp = f"{w_type} №{m['num']} (Пред: {prev_val})"
                self.combo_meter.addItem(disp, userData=m)
        self.combo_meter.blockSignals(False)
        self._on_meter_selected()

    def _on_meter_selected(self):
        m_data = self.combo_meter.currentData()
        if m_data:
            prev_val = m_data.get('prev', 0.0)
            self.txt_final.setText(str(prev_val))

    def _add_replacement(self):
        apt = self.combo_apt.currentData() or self.combo_apt.currentText().replace(" [✓ Замена]", "")
        m_data = self.combo_meter.currentData()
        if not apt or not m_data:
            return

        try:
            fin_val = float(self.txt_final.text().replace(',', '.'))
            init_val = float(self.txt_initial.text().replace(',', '.'))
        except ValueError:
            return

        w_type = m_data['type']
        m_num = m_data['num']

        self.closed_records = [r for r in self.closed_records if not (r.apartment == apt and r.water_type == w_type and r.meter_num == m_num)]
        self.new_records = [r for r in self.new_records if not (r.apartment == apt and r.water_type == w_type and r.meter_num == m_num)]

        self.closed_records.append(ClosedMeterRecord(apartment=apt, water_type=w_type, meter_num=m_num, final_reading=fin_val))
        self.new_records.append(NewMeterRecord(apartment=apt, water_type=w_type, meter_num=m_num, initial_reading=init_val))

        self._populate_apartments(self.search_edit.text())
        self._refresh_list_view()

    def _refresh_list_view(self):
        """Рендеринг карточек замен в виде матовых капсул с бейджами типа воды."""
        while self.scroll_layout.count() > 1:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for c_rec in self.closed_records:
            n_rec = next((r for r in self.new_records if r.apartment == c_rec.apartment and r.water_type == c_rec.water_type and r.meter_num == c_rec.meter_num), None)

            card = QFrame()
            card.setObjectName("GlassCard")
            c_lay = QHBoxLayout(card)
            c_lay.setContentsMargins(12, 8, 12, 8)
            c_lay.setSpacing(10)

            # Бейдж капли для ХВС / пламени для ГВС
            is_cold = (c_rec.water_type == 'cold')
            badge_icon_name = "droplet" if is_cold else "flame"
            curr_theme = ThemeManager.get_current_theme_name()
            is_light = curr_theme in ("Pearl Light", "Как дома")
            accent_col = ThemeManager.get_current_accent_color()

            if curr_theme == "Как дома":
                badge_color = "#0A246A" if is_cold else "#C2410C"
                text_col = "#000000"
            elif curr_theme == "Pearl Light":
                badge_color = "#028090" if is_cold else "#D97706"
                text_col = "#0F172A"
            else:
                badge_color = accent_col if is_cold else "#FB923C"
                text_col = "#F8FAFC"
            w_str = "ХВС" if is_cold else "ГВС"

            lbl_badge = QLabel()
            lbl_badge.setPixmap(get_svg_icon(badge_icon_name, color=badge_color).pixmap(18, 18))
            lbl_badge.setStyleSheet("background: transparent;")

            init_str = f" ➔ Нов: <b>{n_rec.initial_reading:.3f}</b>" if n_rec else ""
            txt = (f"<b>{c_rec.apartment}</b> | <span style='color: {badge_color}; font-weight: bold;'>{w_str} №{c_rec.meter_num}</span> "
                   f"(Закр: <b>{c_rec.final_reading:.3f}</b>{init_str})")

            lbl = QLabel(txt)
            lbl.setStyleSheet(f"color: {text_col}; background: transparent; font-size: 13px;")

            # Кнопка Редактировать
            btn_edit = QPushButton(objectName="SecondaryButton")
            btn_edit.setIcon(get_svg_icon("edit"))
            btn_edit.setToolTip("Редактировать замену")
            btn_edit.setFixedSize(28, 28)
            btn_edit.clicked.connect(lambda _, r=c_rec: self._edit_record(r))

            # Кнопка Удалить
            btn_del = QPushButton(objectName="DangerButton")
            btn_del.setIcon(get_svg_icon("trash", color="#F87171"))
            btn_del.setToolTip("Удалить запись")
            btn_del.setFixedSize(28, 28)
            btn_del.clicked.connect(lambda _, r=c_rec: self._remove_record(r))

            c_lay.addWidget(lbl_badge)
            c_lay.addWidget(lbl, 1)
            c_lay.addWidget(btn_edit)
            c_lay.addWidget(btn_del)

            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, card)

    def _edit_record(self, record: ClosedMeterRecord):
        """Подставляет значения записи замены в поля ввода."""
        for i in range(self.combo_apt.count()):
            if self.combo_apt.itemData(i) == record.apartment:
                self.combo_apt.setCurrentIndex(i)
                break

        for i in range(self.combo_meter.count()):
            m_data = self.combo_meter.itemData(i)
            if m_data and m_data.get('type') == record.water_type and m_data.get('num') == record.meter_num:
                self.combo_meter.setCurrentIndex(i)
                break

        self.txt_final.setText(str(record.final_reading))

        n_rec = next((r for r in self.new_records if r.apartment == record.apartment and r.water_type == record.water_type and r.meter_num == record.meter_num), None)
        if n_rec:
            self.txt_initial.setText(str(n_rec.initial_reading))

        ToastNotification.show_toast(self, f"Данные для {record.apartment} подставлены в поля", "INFO")

    def _remove_record(self, record: ClosedMeterRecord):
        self.closed_records = [r for r in self.closed_records if r != record]
        self.new_records = [r for r in self.new_records if not (r.apartment == record.apartment and r.water_type == record.water_type and r.meter_num == record.meter_num)]
        self._populate_apartments(self.search_edit.text())
        self._refresh_list_view()

    def _reset_all(self):
        """Полный сброс всех замен с подтверждением."""
        if not self.closed_records:
            return
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Подтверждение сброса")
        dlg.setText("Вы действительно хотите удалить все зафиксированные замены?")
        dlg.setIcon(QMessageBox.Icon.Question)
        dlg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        dlg.setDefaultButton(QMessageBox.StandardButton.No)
        if dlg.exec() == QMessageBox.StandardButton.Yes:
            self.closed_records.clear()
            self.new_records.clear()
            self._populate_apartments(self.search_edit.text())
            self._refresh_list_view()
            ToastNotification.show_toast(self, "Все замены сброшены", "INFO")

    def get_results(self):
        return self.closed_records, self.new_records