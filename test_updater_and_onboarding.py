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

    def test_app_version_is_1_2_1(self):
        self.assertEqual(APP_VERSION, "1.2.11")

    def test_version_parsing(self):
        self.assertEqual(parse_version("1.0.0"), (1, 0, 0))
        self.assertEqual(parse_version("v1.0.0"), (1, 0, 0))
        self.assertEqual(parse_version("2.6.0"), (2, 6, 0))
        self.assertEqual(parse_version("v2.6.0"), (2, 6, 0))
        self.assertEqual(parse_version("V3.1.4"), (3, 1, 4))
        self.assertEqual(parse_version("v2.6.1-patch1"), (2, 6, 1))
        self.assertEqual(parse_version("v2.6.0+build123"), (2, 6, 0))
        self.assertEqual(parse_version("10.0"), (10, 0))
        self.assertEqual(parse_version(""), (0, 0, 0))

    def test_version_comparison(self):
        # Новые версии
        self.assertTrue(is_newer_version("1.0.0", "1.0.1"))
        self.assertTrue(is_newer_version("1.0.0", "v1.1.0"))
        self.assertTrue(is_newer_version("1.0.0", "2.0.0"))
        self.assertTrue(is_newer_version("2.5.0", "2.6.0"))

        # Одинаковые или более старые версии
        self.assertFalse(is_newer_version("1.0.0", "1.0.0"))
        self.assertFalse(is_newer_version("v1.0.0", "1.0.0"))
        self.assertFalse(is_newer_version("1.1.0", "1.0.0"))


class TestI18nAndWelcomeSetup(unittest.TestCase):
    """Тестирование локализации и мастера первичной настройки."""

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def test_i18n_manager(self):
        from services.i18n_service import I18nManager, tr
        i18n = I18nManager.instance()
        i18n.set_language("ru")
        self.assertEqual(i18n.current_language, "ru")
        self.assertIn("Добро пожаловать", tr("welcome_title"))

        i18n.set_language("en")
        self.assertEqual(i18n.current_language, "en")
        self.assertIn("Welcome", tr("welcome_title"))

        # Возвращаем ru
        i18n.set_language("ru")

    def test_welcome_dialog_lifecycle(self):
        from ui.dialogs.welcome_dialog import WelcomeSetupDialog
        dlg = WelcomeSetupDialog()
        self.assertEqual(len(dlg.theme_cards), 6)
        dlg._on_theme_selected("Pearl Light")
        from ui.styles import ThemeManager
        self.assertEqual(ThemeManager.get_current_theme_name(), "Pearl Light")
        # Возвращаем Dark Tech Azure
        dlg._on_theme_selected("Dark Tech Azure")
        self.assertEqual(ThemeManager.get_current_theme_name(), "Dark Tech Azure")


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


class TestVersionManagerAndCrashGuard(unittest.TestCase):
    """Тестирование модульной версионности, отката и Crash Guard."""

    def test_version_manager_installed_versions(self):
        from services.updater_service import VersionManager
        versions = VersionManager.get_installed_versions()
        self.assertIn(APP_VERSION, versions)

    def test_version_manager_active_version(self):
        from services.updater_service import VersionManager
        VersionManager.set_active_version(APP_VERSION)
        self.assertEqual(VersionManager.get_active_version(), APP_VERSION)

    def test_crash_guard_flow(self):
        from services.updater_service import VersionManager
        # 1. Запуск
        VersionManager.crash_guard_mark_starting(APP_VERSION)
        # 2. Успех
        VersionManager.crash_guard_mark_success()
        # 3. Проверка отсутствия сбоя
        crashed = VersionManager.crash_guard_check_crashed()
        self.assertIsNone(crashed)


if __name__ == "__main__":
    unittest.main()



