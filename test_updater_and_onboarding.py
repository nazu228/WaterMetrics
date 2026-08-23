"""
test_updater_and_onboarding.py
Автоматические тесты для модуля удаленных обновлений (GitHub Releases)
и интерактивного мастера первой проводки (Onboarding).
"""

import os
import sys
import unittest

# Добавляем путь к корневой директории
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings

from config import APP_VERSION, DEMO_TEMPLATE_FILENAME, DEMO_ARCUS_FILENAME
from services.updater_service import (
    parse_version, is_newer_version, GitHubReleaseInfo
)


class TestUpdaterService(unittest.TestCase):
    """Тестирование парсинга версий и логики обновлений."""

    def test_version_parsing(self):
        self.assertEqual(parse_version("2.6.0"), (2, 6, 0))
        self.assertEqual(parse_version("v2.6.0"), (2, 6, 0))
        self.assertEqual(parse_version("V3.1.4"), (3, 1, 4))
        self.assertEqual(parse_version("v2.6.1-patch1"), (2, 6, 1))
        self.assertEqual(parse_version("v2.6.0+build123"), (2, 6, 0))
        self.assertEqual(parse_version("10.0"), (10, 0))
        self.assertEqual(parse_version(""), (0, 0, 0))

    def test_version_comparison(self):
        # Новые версии
        self.assertTrue(is_newer_version("2.5.0", "2.6.0"))
        self.assertTrue(is_newer_version("2.6.0", "v2.6.1"))
        self.assertTrue(is_newer_version("2.6.0", "3.0.0"))
        self.assertTrue(is_newer_version("1.9.9", "2.0.0"))
        self.assertTrue(is_newer_version("2.6", "2.6.1"))

        # Одинаковые или более старые версии
        self.assertFalse(is_newer_version("2.6.0", "2.6.0"))
        self.assertFalse(is_newer_version("v2.6.0", "2.6.0"))
        self.assertFalse(is_newer_version("2.6.1", "2.6.0"))
        self.assertFalse(is_newer_version("3.0.0", "2.9.9"))


class TestOnboardingAndDemoData(unittest.TestCase):
    """Тестирование демо-данных и онбординга."""

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_demo_files_exist(self):
        tpl_path = os.path.join(BASE_DIR, DEMO_TEMPLATE_FILENAME)
        arc_path = os.path.join(BASE_DIR, DEMO_ARCUS_FILENAME)
        self.assertTrue(os.path.exists(tpl_path), f"Файл шаблона {tpl_path} должен существовать")
        self.assertTrue(os.path.exists(arc_path), f"Файл аркуса {arc_path} должен существовать")

    def test_load_demo_data_in_dashboard(self):
        from ui.dashboard_page import MainDashboardPage
        dash = MainDashboardPage()
        ok = dash.load_demo_data()
        self.assertTrue(ok, "load_demo_data() должен возвращать True")
        self.assertTrue(os.path.exists(dash.drop_tpl.file_path))
        self.assertTrue(os.path.exists(dash.drop_arc.file_path))
        self.assertEqual(dash.txt_cold.text(), "110.0")
        self.assertEqual(dash.txt_hot.text(), "75.0")
        self.assertEqual(dash.txt_corr.text(), "0.0")
        self.assertTrue(len(dash.txt_save.text()) > 0)

    def test_onboarding_overlay_flow(self):
        from ui.components.onboarding_overlay import OnboardingOverlay, OnboardingStep
        from PySide6.QtWidgets import QWidget

        parent_w = QWidget()
        parent_w.resize(800, 600)

        target1 = QWidget(parent_w)
        target2 = QWidget(parent_w)

        steps = [
            OnboardingStep("Шаг 1", "Описание 1", lambda: target1, show_demo_btn=True),
            OnboardingStep("Шаг 2", "Описание 2", lambda: target2, show_demo_btn=False),
        ]

        overlay = OnboardingOverlay(parent_w, steps)
        overlay.start()
        self.assertEqual(overlay.current_step_idx, 0)
        self.assertFalse(overlay.btn_demo.isHidden())

        overlay.next_step()
        self.assertEqual(overlay.current_step_idx, 1)
        self.assertTrue(overlay.btn_demo.isHidden())

        overlay.prev_step()
        self.assertEqual(overlay.current_step_idx, 0)
        self.assertFalse(overlay.btn_demo.isHidden())

        overlay.finish_tour()
        self.assertTrue(overlay.isHidden())

    def test_calculation_with_demo_data(self):
        from core.excel_parser import ExcelManager
        from core.calculator import WaterCalculator
        from models import CalculationConfig
        import tempfile

        tpl_path = os.path.join(BASE_DIR, DEMO_TEMPLATE_FILENAME)
        arc_path = os.path.join(BASE_DIR, DEMO_ARCUS_FILENAME)
        temp_out = os.path.join(tempfile.gettempdir(), "test_demo_calc_out.xlsx")

        excel_mgr = ExcelManager()
        wb, ws, meters, meter_by_type, all_rows, non_apts, name_col = excel_mgr.extract_data(
            tpl_path, arc_path
        )

        config = CalculationConfig(
            target_cold=110.0,
            target_hot=75.0,
            add_hvs=0.0,
            norm_cold=4.04,
            norm_hot=2.65,
            template_path=tpl_path,
            arcus_path=arc_path,
            save_path=temp_out,
            closed_meters=[],
            new_meters=[]
        )

        calc = WaterCalculator(config, lambda msg, level="INFO": None, lambda msg: True)
        calc.calculate(all_rows, meters, meter_by_type)

        excel_mgr.save_result(
            wb, ws, temp_out, meters, all_rows, non_apts, name_col, [], []
        )

        self.assertTrue(os.path.exists(temp_out))
        self.assertTrue(os.path.getsize(temp_out) > 0)
        try:
            os.remove(temp_out)
        except Exception:
            pass


if __name__ == "__main__":
    unittest.main()

