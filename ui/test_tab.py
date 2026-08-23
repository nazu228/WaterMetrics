"""
Модуль сквозного визуального GUI E2E-автотестирования.
Использует векторные SVG-иконки для управляющих кнопок.
"""

import os
import sys
import subprocess
import threading
import traceback
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import openpyxl

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PySide6.QtCore import QThread, Signal, Qt, Slot
from PySide6.QtGui import QColor

from core.calculator import WaterCalculator
from core.excel_parser import ExcelManager
from models import CalculationConfig, ClosedMeterRecord, NewMeterRecord
from ui.components.interactive import HoverGlassCard
from ui.components.toast import ToastNotification
from ui.styles import get_svg_icon

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_RESULTS_DIR = os.path.join(BASE_DIR, "test_results")


class GuiTestWorker(QThread):
    """Фоновый оркестратор сквозного GUI E2E-теста."""
    log_signal = Signal(str, str)
    file_created_signal = Signal(str, str, str)
    finished_signal = Signal(bool, str)

    gui_setup_signal = Signal(dict)
    trigger_calc_signal = Signal()
    gui_cleanup_signal = Signal()
    switch_page_signal = Signal(int)

    def __init__(self, main_win=None, parent=None):
        super().__init__(parent)
        self.main_win = main_win
        self.calc_event = threading.Event()

    def notify_calc_finished(self):
        self.calc_event.set()

    def run(self):
        try:
            self.log("[GUI E2E] Старт визуального тестирования...", "INFO")
            os.makedirs(TEST_RESULTS_DIR, exist_ok=True)

            if not self.main_win:
                self.finished_signal.emit(False, "MainWin недоступен.")
                return

            template_path, arcus_path = self._find_input_files()
            if not template_path or not arcus_path:
                self.log("Ошибка: Входные файлы Excel не найдены!", "ERROR")
                self.log("Пожалуйста, выберите файлы Шаблона и Аркуса на главном Дашборде перед запуском теста.", "INFO")
                self.finished_signal.emit(False, "Входные файлы не найдены.")
                return

            self.log(f"Используется шаблон: {os.path.basename(template_path)}", "INFO")
            self.log(f"Используется аркус: {os.path.basename(arcus_path)}", "INFO")

            excel_mgr = getattr(self.main_win, 'excel_manager', ExcelManager())
            apts_data = excel_mgr.extract_apartments_and_meters(template_path)
            target_apt, target_meter = self._select_apartment_for_replacement(apts_data)

            closed_recs, new_recs = [], []
            if target_apt and target_meter:
                m_type = target_meter.get('type', 'cold')
                m_num = target_meter.get('num', 1)
                prev_val = float(target_meter.get('prev', 0.0) or 0.0)

                closed_recs.append(ClosedMeterRecord(apartment=target_apt, water_type=m_type, meter_num=m_num, final_reading=prev_val))
                new_recs.append(NewMeterRecord(apartment=target_apt, water_type=m_type, meter_num=m_num, initial_reading=0.0))

            self.switch_page_signal.emit(0)
            QThread.msleep(600)

            base_output_filename = excel_mgr.parse_house_and_next_month(template_path)

            # Прогон 1
            timestamp = datetime.now().strftime("%H%M%S")
            file_1_name = f"GUI_E2E_Plus100_{base_output_filename}"
            save_path_1 = os.path.join(TEST_RESULTS_DIR, file_1_name)

            if os.path.exists(save_path_1):
                try:
                    os.rename(save_path_1, save_path_1)
                except OSError:
                    base_n, ext_n = os.path.splitext(base_output_filename)
                    file_1_name = f"GUI_E2E_Plus100_{base_n}_{timestamp}{ext_n}"
                    save_path_1 = os.path.join(TEST_RESULTS_DIR, file_1_name)

            gui_data_1 = {
                'tpl': template_path, 'arc': arcus_path, 'save': save_path_1,
                'cold': "500.0", 'hot': "400.0", 'corr': "100.0",
                'closed_meters': closed_recs, 'new_meters': new_recs
            }
            self.gui_setup_signal.emit(gui_data_1)
            QThread.msleep(800)

            self.calc_event.clear()
            self.trigger_calc_signal.emit()

            if not self.calc_event.wait(timeout=90):
                raise TimeoutError("Превышено время ожидания расчёта.")

            audit_1_ok = self._audit_excel_file(save_path_1)
            self.file_created_signal.emit(file_1_name, "PASSED" if audit_1_ok else "ERR", save_path_1)

            self.gui_cleanup_signal.emit()
            self.switch_page_signal.emit(3)
            self.finished_signal.emit(True, "GUI E2E-тест пройден!")

        except Exception as e:
            self.log(f"Ошибка E2E-теста: {e}", "ERROR")
            self.gui_cleanup_signal.emit()
            self.switch_page_signal.emit(3)
            self.finished_signal.emit(False, str(e))

    def _select_apartment_for_replacement(self, apts_data):
        if not apts_data:
            return None, None
        for apt_name, meter_list in apts_data.items():
            if isinstance(meter_list, list) and len(meter_list) >= 2:
                return apt_name, meter_list[0]
        first_apt = next(iter(apts_data.keys()))
        return first_apt, apts_data[first_apt][0] if apts_data[first_apt] else None

    def _audit_excel_file(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            return False
        try:
            wb = openpyxl.load_workbook(file_path, data_only=False)
            ws = wb.active
            itogo_found = any("итого" in " ".join([str(v) for v in row if v]).lower() for row in ws.iter_rows(values_only=True))
            wb.close()
            return itogo_found
        except Exception:
            return False

    def _find_input_files(self):
        """
        Умный поиск входных файлов:
        1. Сначала проверяются файлы, выбранные пользователем на Главном Дашборде.
        2. Затем проверяются файлы по известным именам шаблонов.
        3. В качестве фоллбэка используются любые найденные .xlsx файлы в проекте.
        """
        if self.main_win and hasattr(self.main_win, 'page_main'):
            dash = self.main_win.page_main
            tpl_dash = getattr(dash.drop_tpl, 'file_path', None) if hasattr(dash, 'drop_tpl') else None
            arc_dash = getattr(dash.drop_arc, 'file_path', None) if hasattr(dash, 'drop_arc') else None

            if tpl_dash and os.path.exists(tpl_dash) and arc_dash and os.path.exists(arc_dash):
                return tpl_dash, arc_dash

        template_candidates = ["45 .xlsx", "45.xlsx", "Душистая 45+.xlsx", "2я Целиноградская 1.xlsx", "Шаблон.xlsx"]
        arcus_candidates = ["45+.xlsx", "душ 45 аркус.xlsx", "Аркус.xlsx"]

        tpl_path = next((os.path.join(BASE_DIR, n) for n in template_candidates if os.path.exists(os.path.join(BASE_DIR, n))), None)
        arc_path = next((os.path.join(BASE_DIR, n) for n in arcus_candidates if os.path.exists(os.path.join(BASE_DIR, n))), None)

        if tpl_path and arc_path:
            return tpl_path, arc_path

        all_xlsx = [os.path.join(BASE_DIR, f) for f in os.listdir(BASE_DIR) if f.lower().endswith('.xlsx') and not f.startswith('~$')]
        if len(all_xlsx) >= 2:
            return all_xlsx[0], all_xlsx[1]
        elif len(all_xlsx) == 1:
            return all_xlsx[0], all_xlsx[0]

        return None, None

    def log(self, msg: str, level: str = "INFO"):
        self.log_signal.emit(msg, level)


class AutoTestsPage(QWidget):
    """Страница автотестирования."""

    def __init__(self, main_win=None):
        super().__init__()
        self.main_win = main_win
        self.worker = None
        self.setObjectName("AutoTestsPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Визуальное GUI E2E-Тестирование", objectName="PageTitle")
        title.setWordWrap(False)
        layout.addWidget(title)

        card = HoverGlassCard()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(14)

        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(12)

        self.btn_run = QPushButton("Запустить E2E-Тест", objectName="PrimaryButton")
        self.btn_run.setIcon(get_svg_icon("tests", color="#020617"))
        self.btn_run.setFixedHeight(38)
        self.btn_run.clicked.connect(self.run_gui_e2e_test)

        self.btn_open_file = QPushButton("Открыть выбранный файл", objectName="SecondaryButton")
        self.btn_open_file.setIcon(get_svg_icon("folder"))
        self.btn_open_file.setFixedHeight(38)
        self.btn_open_file.clicked.connect(self.open_selected_file)

        self.btn_delete = QPushButton("Удалить результаты", objectName="DangerButton")
        self.btn_delete.setIcon(get_svg_icon("trash", color="#F87171"))
        self.btn_delete.setFixedHeight(38)
        self.btn_delete.clicked.connect(self.delete_results)

        ctrl_layout.addWidget(self.btn_run)
        ctrl_layout.addWidget(self.btn_open_file)
        ctrl_layout.addWidget(self.btn_delete)
        ctrl_layout.addStretch()

        card_layout.addLayout(ctrl_layout)

        content_grid = QGridLayout()
        content_grid.setSpacing(14)

        lbl_table = QLabel("Сформированные тестовые файлы Excel:", objectName="SectionTitle")
        content_grid.addWidget(lbl_table, 0, 0)

        self.table_hist = QTableWidget(0, 3)
        self.table_hist.setHorizontalHeaderLabels(["Имя файла", "Статус", "Путь"])
        self.table_hist.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_hist.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_hist.horizontalHeader().setFixedHeight(32)
        self.table_hist.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table_hist.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_hist.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        content_grid.addWidget(self.table_hist, 1, 0)

        lbl_logs = QLabel("Протокол GUI-эмуляции:", objectName="SectionTitle")
        content_grid.addWidget(lbl_logs, 0, 1)

        self.test_log = QTextEdit()
        self.test_log.setObjectName("LogViewer")
        self.test_log.setReadOnly(True)
        self.test_log.append('<span style="color: #00F2FE;"><b>[SYSTEM]</b> Нажмите "Запустить E2E-Тест" для старта проверки.</span>')

        content_grid.addWidget(self.test_log, 1, 1)

        content_grid.setColumnStretch(0, 1)
        content_grid.setColumnStretch(1, 1)

        card_layout.addLayout(content_grid, 1)
        layout.addWidget(card, 1)

    def run_gui_e2e_test(self):
        if not self.main_win:
            return

        self.btn_run.setEnabled(False)
        self.worker = GuiTestWorker(self.main_win, self)
        self.worker.log_signal.connect(self.log_from_worker)
        self.worker.file_created_signal.connect(self.add_test_file_entry)
        self.worker.finished_signal.connect(self.test_finished)

        self.worker.gui_setup_signal.connect(self.on_gui_setup)
        self.worker.trigger_calc_signal.connect(self.on_trigger_calc)
        self.worker.gui_cleanup_signal.connect(self.on_gui_cleanup)
        self.worker.switch_page_signal.connect(self.on_switch_page)

        self.worker.start()

    @Slot(dict)
    def on_gui_setup(self, data: dict):
        if not self.main_win or not hasattr(self.main_win, 'page_main'):
            return
        dash = self.main_win.page_main
        if hasattr(dash, 'drop_tpl'): dash.drop_tpl.set_file_path(data.get('tpl', ''))
        if hasattr(dash, 'drop_arc'): dash.drop_arc.set_file_path(data.get('arc', ''))
        if hasattr(dash, 'txt_save'): dash.txt_save.setText(data.get('save', ''))
        if hasattr(dash, 'txt_cold'): dash.txt_cold.setText(data.get('cold', '0.0'))
        if hasattr(dash, 'txt_hot'): dash.txt_hot.setText(data.get('hot', '0.0'))
        if hasattr(dash, 'txt_corr'): dash.txt_corr.setText(data.get('corr', '0'))
        self.main_win.closed_meters = data.get('closed_meters', [])
        self.main_win.new_meters = data.get('new_meters', [])

    @Slot()
    def on_trigger_calc(self):
        if self.main_win:
            self.main_win.run_calculation()
            if hasattr(self.main_win, 'calc_worker') and self.main_win.calc_worker:
                self.main_win.calc_worker.finished_signal.connect(lambda *args: self.worker.notify_calc_finished() if self.worker else None)
            else:
                if self.worker:
                    self.worker.notify_calc_finished()

    @Slot()
    def on_gui_cleanup(self):
        if self.main_win and hasattr(self.main_win, 'page_main'):
            dash = self.main_win.page_main
            dash.txt_cold.setText("0.0")
            dash.txt_hot.setText("0.0")
            dash.txt_corr.setText("0")
            self.main_win.closed_meters = []
            self.main_win.new_meters = []

    @Slot(int)
    def on_switch_page(self, idx: int):
        if self.main_win and hasattr(self.main_win, 'switch_page'):
            self.main_win.switch_page(idx)

    def log_from_worker(self, msg: str, level: str):
        colors = {"INFO": "#00F2FE", "SUCCESS": "#10B981", "ERROR": "#EF4444"}
        c = colors.get(level.upper(), "#F8FAFC")
        self.test_log.append(f'<span style="color: {c};">{msg}</span>')

    def add_test_file_entry(self, filename: str, status: str, full_path: str):
        row = self.table_hist.rowCount()
        self.table_hist.insertRow(row)

        item_name = QTableWidgetItem(filename)
        item_status = QTableWidgetItem(status)
        item_status.setForeground(QColor("#10B981") if "PASSED" in status else QColor("#00F2FE"))
        item_path = QTableWidgetItem(full_path)

        self.table_hist.setItem(row, 0, item_name)
        self.table_hist.setItem(row, 1, item_status)
        self.table_hist.setItem(row, 2, item_path)

    def open_selected_file(self):
        row = self.table_hist.currentRow()
        if row >= 0:
            path_item = self.table_hist.item(row, 2)
            if path_item and os.path.exists(path_item.text()):
                file_path = os.path.abspath(path_item.text())
                try:
                    if sys.platform == 'win32':
                        os.startfile(file_path)
                    elif sys.platform == 'darwin':
                        subprocess.Popen(['open', file_path])
                    else:
                        subprocess.Popen(['xdg-open', file_path])
                except Exception as e:
                    ToastNotification.show_toast(self, f"Не удалось открыть файл: {e}", "ERROR")
            else:
                ToastNotification.show_toast(self, "Выбранный файл не найден на диске!", "ERROR")

    def delete_results(self):
        if os.path.exists(TEST_RESULTS_DIR):
            for f in os.listdir(TEST_RESULTS_DIR):
                try: os.remove(os.path.join(TEST_RESULTS_DIR, f))
                except Exception: pass
        self.table_hist.setRowCount(0)
        self.test_log.clear()

    def test_finished(self, success: bool, msg: str):
        self.btn_run.setEnabled(True)
        ToastNotification.show_toast(self.main_win if self.main_win else self, "E2E-тест завершен!", "SUCCESS" if success else "ERROR")