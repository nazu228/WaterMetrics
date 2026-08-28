"""
ui/dialogs/replacement_dialog.py — Премиальный безрамочный Мастер замен счетчиков (WaterMetrics).

Реализует:
1. Безрамочный стеклянный дизайн (Frameless Glassmorphism) без системной белой окантовки.
2. Свободное перетаскивание окна за шапку или фон.
3. 100% сохранение всех функций:
   - Полнотекстовый и цифровой поиск помещений с естественной сортировкой (Natural Sorting).
   - Индикаторы `[✓ Замена]` у квартир с уже зафиксированными заменами.
   - Выбор прибора с отображением предыдущих показаний.
   - Поля финального и начального показаний с числовой валидацией.
   - Добавление, редактирование (подстановка в поля ввода), единичное удаление и полный сброс с подтверждением.
   - Матовые интерактивные капсулы зафиксированных замен с иконками ХВС/ГВС и бейджами показаний.
   - Адаптация под все темные и светлые темы оформления.
"""

from __future__ import annotations

import re
from typing import List, Dict, Tuple, Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QScrollArea, QWidget, QFrame, QMessageBox, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, Slot, QPoint, QSize, QEvent
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QLinearGradient, QPainterPath

from models import ClosedMeterRecord, NewMeterRecord
from ui.styles import get_svg_icon, ThemeManager
from ui.components.glass_icon import GlassIconWidget
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
    """
    Премиальный безрамочный Мастер замен ИПУ с поиском,
    редактированием и динамической фильтрацией.
    """

    def __init__(self, parent=None, apts_data=None, closed_meters=None, new_meters=None):
        super().__init__(parent)
        self.setWindowTitle("Мастер замен счетчиков ИПУ")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Dialog
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(720, 640)

        self.apts_data = apts_data or {}
        self.closed_records = list(closed_meters or [])
        self.new_records = list(new_meters or [])
        self._drag_pos: Optional[QPoint] = None

        self.init_ui()

    def paintEvent(self, event):
        """Отрисовка премиального матового фона со скругленными углами и неоновым контуром."""
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
            border_color = QColor(accent)
            border_color.setAlpha(200)
            glow_pen = QPen(border_color, 1.8)
        else:
            grad = QLinearGradient(0, 0, 0, rect.height())
            grad.setColorAt(0.0, QColor(18, 28, 50, 252))
            grad.setColorAt(1.0, QColor(15, 23, 42, 252))
            border_color = QColor(accent)
            border_color.setAlpha(180)
            glow_pen = QPen(border_color, 1.8)

        painter.setPen(glow_pen)
        painter.setBrush(QBrush(grad))
        painter.drawPath(path)

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 16, 20, 18)
        root_layout.setSpacing(12)

        accent = ThemeManager.get_current_accent_color()
        curr_theme = ThemeManager.get_current_theme_name()
        is_light = curr_theme in ("Pearl Light", "Как дома")

        # ─── 1. ШАПКА ДИАЛОГА (КАСТОМНЫЙ TITLEBAR) ──────────────────────────
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        self.icon_badge = GlassIconWidget("replace", color=accent, size=QSize(36, 36))
        header_row.addWidget(self.icon_badge)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)

        self.lbl_main_title = QLabel("Мастер замен счетчиков ИПУ")
        title_color = "#0A246A" if curr_theme == "Как дома" else ("#0F172A" if is_light else "#F8FAFC")
        self.lbl_main_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {title_color}; background: transparent;")

        self.lbl_subtitle = QLabel("Управление закрытыми и вновь установленными приборами учета")
        self.lbl_subtitle.setStyleSheet("font-size: 12.5px; color: #94A3B8; background: transparent;")

        title_vbox.addWidget(self.lbl_main_title)
        title_vbox.addWidget(self.lbl_subtitle)
        header_row.addLayout(title_vbox, 1)

        # Кнопка закрытия [✕]
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setToolTip("Закрыть окно (Esc)")
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                color: #94A3B8;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.25);
                color: #EF4444;
                border: 1px solid rgba(239, 68, 68, 0.5);
            }
        """)
        self.btn_close.clicked.connect(self.reject)
        header_row.addWidget(self.btn_close)

        root_layout.addLayout(header_row)

        # ─── 2. ФОРМА ДОБАВЛЕНИЯ / РЕДАКТИРОВАНИЯ ───────────────────────────
        form_card = QFrame()
        form_card.setObjectName("GlassCard")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(14, 12, 14, 12)
        form_layout.setSpacing(10)

        # Поиск помещения
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        lbl_search_icon = QLabel()
        lbl_search_icon.setPixmap(get_svg_icon("search", color=accent).pixmap(18, 18))
        lbl_search_icon.setStyleSheet("background: transparent;")
        search_row.addWidget(lbl_search_icon)

        lbl_search = QLabel("Поиск помещения:", objectName="FieldLabel")
        lbl_search.setStyleSheet("font-size: 13px; font-weight: bold; color: #94A3B8; background: transparent;")
        search_row.addWidget(lbl_search)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Введите номер квартиры или название...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setMinimumHeight(34)
        self.search_edit.setStyleSheet("font-size: 13.5px;")
        self.search_edit.textChanged.connect(self._on_search_text_changed)
        search_row.addWidget(self.search_edit, 1)
        form_layout.addLayout(search_row)

        # Выбор квартиры и прибора в 2 колонки
        select_grid = QHBoxLayout()
        select_grid.setSpacing(12)

        # Колонка Квартира
        col_apt = QVBoxLayout()
        col_apt.setSpacing(4)
        lbl_apt = QLabel("Квартира / Помещение:", objectName="FieldLabel")
        lbl_apt.setStyleSheet("font-size: 13px; font-weight: bold; color: #94A3B8; background: transparent;")
        self.combo_apt = QComboBox()
        self.combo_apt.setMinimumHeight(34)
        self.combo_apt.setStyleSheet("font-size: 13px;")
        self.combo_apt.currentTextChanged.connect(self._update_meters_combo)
        col_apt.addWidget(lbl_apt)
        col_apt.addWidget(self.combo_apt)
        select_grid.addLayout(col_apt, 1)

        # Колонка Прибор
        col_meter = QVBoxLayout()
        col_meter.setSpacing(4)
        lbl_meter = QLabel("Прибор учета:", objectName="FieldLabel")
        lbl_meter.setStyleSheet("font-size: 13px; font-weight: bold; color: #94A3B8; background: transparent;")
        self.combo_meter = QComboBox()
        self.combo_meter.setMinimumHeight(34)
        self.combo_meter.setStyleSheet("font-size: 13px;")
        self.combo_meter.currentIndexChanged.connect(self._on_meter_selected)
        col_meter.addWidget(lbl_meter)
        col_meter.addWidget(self.combo_meter)
        select_grid.addLayout(col_meter, 1)

        form_layout.addLayout(select_grid)

        # Показания (Финальное старого и Начальное нового)
        readings_grid = QHBoxLayout()
        readings_grid.setSpacing(12)

        col_fin = QVBoxLayout()
        col_fin.setSpacing(4)
        lbl_fin = QLabel("Финальное показание (старый ИПУ):", objectName="FieldLabel")
        lbl_fin.setStyleSheet("font-size: 13px; font-weight: bold; color: #94A3B8; background: transparent;")
        self.txt_final = QLineEdit("0.0")
        self.txt_final.setMinimumHeight(34)
        self.txt_final.setStyleSheet("font-family: 'Consolas', monospace; font-size: 14px; font-weight: bold;")
        col_fin.addWidget(lbl_fin)
        col_fin.addWidget(self.txt_final)
        readings_grid.addLayout(col_fin, 1)

        col_init = QVBoxLayout()
        col_init.setSpacing(4)
        lbl_init = QLabel("Начальное показание (новый ИПУ):", objectName="FieldLabel")
        lbl_init.setStyleSheet("font-size: 13px; font-weight: bold; color: #94A3B8; background: transparent;")
        self.txt_initial = QLineEdit("0.0")
        self.txt_initial.setMinimumHeight(34)
        self.txt_initial.setStyleSheet("font-family: 'Consolas', monospace; font-size: 14px; font-weight: bold;")
        col_init.addWidget(lbl_init)
        col_init.addWidget(self.txt_initial)
        readings_grid.addLayout(col_init, 1)

        form_layout.addLayout(readings_grid)

        # Кнопка Добавить / Обновить
        self.btn_add = QPushButton("+ Добавить / Обновить замену", objectName="PrimaryButton")
        self.btn_add.setIcon(get_svg_icon("plus", color="#020617"))
        self.btn_add.setMinimumHeight(36)
        self.btn_add.setStyleSheet("font-size: 13.5px; font-weight: 800;")
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.clicked.connect(self._add_replacement)
        form_layout.addWidget(self.btn_add)

        root_layout.addWidget(form_card)

        # ─── 3. СПИСОК ЗАФИКСИРОВАННЫХ ЗАМЕН ──────────────────────────────
        list_hdr_layout = QHBoxLayout()
        list_hdr_layout.setSpacing(8)

        self.lbl_list_hdr = QLabel("Зафиксированные замены:", objectName="SectionTitle")
        self.lbl_list_hdr.setStyleSheet("font-size: 14px; font-weight: bold; background: transparent;")
        list_hdr_layout.addWidget(self.lbl_list_hdr)

        self.lbl_count_badge = QLabel("(0)")
        self.lbl_count_badge.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {accent}; background: transparent;")
        list_hdr_layout.addWidget(self.lbl_count_badge)

        list_hdr_layout.addStretch()

        self.btn_reset_all = QPushButton("Сбросить все", objectName="DangerButton")
        self.btn_reset_all.setIcon(get_svg_icon("trash", color="#F87171"))
        self.btn_reset_all.setMinimumHeight(30)
        self.btn_reset_all.setStyleSheet("font-size: 12.5px; font-weight: bold;")
        self.btn_reset_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset_all.clicked.connect(self._reset_all)
        list_hdr_layout.addWidget(self.btn_reset_all)

        root_layout.addLayout(list_hdr_layout)

        # Область прокрутки для карточек замен
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent !important;
                border: 1.5px solid rgba(255, 255, 255, 0.12);
                border-radius: 10px;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent !important;
            }
        """)

        self.scroll_content = QWidget()
        self.scroll_content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(8, 8, 8, 8)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_content)
        root_layout.addWidget(self.scroll_area, 1)

        # ─── 4. НИЖНЯЯ ПАНЕЛЬ ДЕЙСТВИЙ ─────────────────────────────────────
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        self.lbl_footer_info = QLabel("")
        self.lbl_footer_info.setStyleSheet("font-size: 12px; color: #94A3B8; background: transparent;")
        btn_box.addWidget(self.lbl_footer_info)
        btn_box.addStretch()

        self.btn_cancel = QPushButton("Отмена", objectName="SecondaryButton")
        self.btn_cancel.setMinimumHeight(36)
        self.btn_cancel.setMinimumWidth(100)
        self.btn_cancel.setStyleSheet("font-size: 13px; font-weight: 600;")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Сохранить и применить", objectName="PrimaryButton")
        self.btn_save.setIcon(get_svg_icon("save", color="#020617"))
        self.btn_save.setMinimumHeight(36)
        self.btn_save.setMinimumWidth(180)
        self.btn_save.setStyleSheet("font-size: 13.5px; font-weight: 800;")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self.accept)

        btn_box.addWidget(self.btn_cancel)
        btn_box.addWidget(self.btn_save)
        root_layout.addLayout(btn_box)

        self._populate_apartments()
        self._refresh_list_view()

    # ─── ПЕРЕТАСКИВАНИЕ ОКНА МЫШЬЮ ────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
            child = self.childAt(pos)
            is_interactive = False
            w = child
            while w and w is not self:
                if isinstance(w, (QLineEdit, QPushButton, QComboBox, QScrollArea)):
                    is_interactive = True
                    break
                w = w.parentWidget()
            if not is_interactive:
                self._drag_pos = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            curr_pos = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()
            delta = curr_pos - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = curr_pos
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            event.accept()
            return
        super().keyPressEvent(event)

    # ─── ЛОГИКА ФОРМЫ И СПИСКА ────────────────────────────────────────────

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
            ToastNotification.show_toast(self, "Введите корректные числовые показания!", "ERROR")
            return

        w_type = m_data['type']
        m_num = m_data['num']

        self.closed_records = [r for r in self.closed_records if not (r.apartment == apt and r.water_type == w_type and r.meter_num == m_num)]
        self.new_records = [r for r in self.new_records if not (r.apartment == apt and r.water_type == w_type and r.meter_num == m_num)]

        self.closed_records.append(ClosedMeterRecord(apartment=apt, water_type=w_type, meter_num=m_num, final_reading=fin_val))
        self.new_records.append(NewMeterRecord(apartment=apt, water_type=w_type, meter_num=m_num, initial_reading=init_val))

        self._populate_apartments(self.search_edit.text())
        self._refresh_list_view()
        ToastNotification.show_toast(self, f"Замена для {apt} ({w_type.upper()} №{m_num}) сохранена", "SUCCESS")

    def _refresh_list_view(self):
        """Рендеринг карточек замен в виде матовых капсул с бейджами типа воды."""
        while self.scroll_layout.count() > 1:
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        count = len(self.closed_records)
        self.lbl_count_badge.setText(f"({count})")
        self.lbl_footer_info.setText(f"Всего зафиксировано: {count} шт." if count > 0 else "")

        if count == 0:
            placeholder = QLabel("Нет добавленных замен.\nВыберите квартиру и прибор выше, чтобы зафиксировать замену.")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #64748B; font-size: 11px; padding: 24px 0; background: transparent;")
            self.scroll_layout.insertWidget(0, placeholder)
            return

        for c_rec in self.closed_records:
            n_rec = next((r for r in self.new_records if r.apartment == c_rec.apartment and r.water_type == c_rec.water_type and r.meter_num == c_rec.meter_num), None)

            card = QFrame()
            card.setObjectName("GlassCard")
            card.setStyleSheet("""
                QFrame#GlassCard {
                    background: rgba(15, 23, 42, 0.55);
                    border: 1px solid rgba(255, 255, 255, 0.10);
                    border-radius: 8px;
                }
                QFrame#GlassCard:hover {
                    background: rgba(15, 23, 42, 0.75);
                    border: 1px solid rgba(255, 255, 255, 0.22);
                }
            """)
            c_lay = QHBoxLayout(card)
            c_lay.setContentsMargins(10, 6, 10, 6)
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
            lbl_badge.setPixmap(get_svg_icon(badge_icon_name, color=badge_color).pixmap(16, 16))
            lbl_badge.setStyleSheet("background: transparent;")

            init_str = f" ➔ <span style='color: #10B981;'>Нов: <b>{n_rec.initial_reading:.3f}</b></span>" if n_rec else ""
            txt = (f"<b>{c_rec.apartment}</b> | <span style='color: {badge_color}; font-weight: bold;'>{w_str} №{c_rec.meter_num}</span> "
                   f"(<span style='color: #F87171;'>Закр: <b>{c_rec.final_reading:.3f}</b></span>{init_str})")

            lbl = QLabel(txt)
            lbl.setStyleSheet(f"color: {text_col}; background: transparent; font-size: 12px;")

            # Кнопка Редактировать
            btn_edit = QPushButton(objectName="SecondaryButton")
            btn_edit.setIcon(get_svg_icon("edit"))
            btn_edit.setToolTip("Редактировать замену (подставить в поля)")
            btn_edit.setFixedSize(26, 26)
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.clicked.connect(lambda _, r=c_rec: self._edit_record(r))

            # Кнопка Удалить
            btn_del = QPushButton(objectName="DangerButton")
            btn_del.setIcon(get_svg_icon("trash", color="#F87171"))
            btn_del.setToolTip("Удалить запись")
            btn_del.setFixedSize(26, 26)
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
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

    def get_results(self) -> Tuple[List[ClosedMeterRecord], List[NewMeterRecord]]:
        return self.closed_records, self.new_records