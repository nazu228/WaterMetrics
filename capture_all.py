import sys
import os
import time

from PySide6.QtGui import QSurfaceFormat, QIcon
from PySide6.QtWidgets import QApplication, QTableWidgetItem
from PySide6.QtCore import QTimer, Qt

fmt = QSurfaceFormat()
fmt.setVersion(3, 3)
fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
fmt.setSamples(4)
QSurfaceFormat.setDefaultFormat(fmt)

from main import get_asset_path
from ui.main_window import MainWindow
from ui.styles import DARK_AZURE_QSS, ThemeManager
from ui.dialogs.replacement_dialog import MeterReplacementDialog
from ui.dialogs.command_palette import CommandPaletteDialog
from ui.about_page import DonateDialog, BeachRestDialog, get_asset_path as get_about_asset
from ui.components.progress_overlay import CalculationProgressOverlay

OUTPUT_DIR = r"C:\Users\admin\.gemini\antigravity-ide\brain\be74dacc-ff8b-49bc-83c5-2cf791b6d3c2"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def capture_ui():
    app = QApplication.instance() or QApplication(sys.argv)
    ThemeManager.apply_theme("Dark Tech Azure")
    app.setStyleSheet(DARK_AZURE_QSS)

    window = MainWindow()
    window.resize(1300, 850)
    window.show()

    for _ in range(30):
        app.processEvents()
        time.sleep(0.02)

    def grab_and_save(widget, filename):
        path = os.path.join(OUTPUT_DIR, filename)
        pix = widget.grab()
        pix.save(path, "PNG")
        print(f"Saved: {path} ({pix.width()}x{pix.height()})")

    # 1. Dashboard Tab (Default / Idle)
    window.switch_page(0)
    app.processEvents()
    time.sleep(0.15)
    grab_and_save(window, "audit_01_dashboard_dark_azure.png")

    # 2. Dashboard with filled data & history
    try:
        dash = window.page_main
        dash.drop_tpl.set_file_path("C:/WaterMetrics/data/Шаблон_Ведомость_2026.xlsx")
        dash.drop_arc.set_file_path("C:/WaterMetrics/data/Экспорт_Аркус_Август.xlsx")
        dash.txt_save.setText("C:/WaterMetrics/output/Результат_Расчета_Август.xlsx")
        dash.txt_cold.setText("1450.50")
        dash.txt_hot.setText("890.20")
        dash.txt_corr.setText("45.00")
        
        # Populate history table
        dash.table_hist.setRowCount(3)
        dash.table_hist.setItem(0, 0, QTableWidgetItem("Результат_Расчета_Август_2026.xlsx"))
        dash.table_hist.setItem(0, 1, QTableWidgetItem("C:/WaterMetrics/output/Результат_Расчета_Август_2026.xlsx"))
        dash.table_hist.setItem(1, 0, QTableWidgetItem("Ведомость_Июль_2026_Финальная.xlsx"))
        dash.table_hist.setItem(1, 1, QTableWidgetItem("C:/WaterMetrics/output/Ведомость_Июль_2026_Финальная.xlsx"))
        dash.table_hist.setItem(2, 0, QTableWidgetItem("Тестовый_Расчет_Июнь.xlsx"))
        dash.table_hist.setItem(2, 1, QTableWidgetItem("C:/WaterMetrics/output/Тестовый_Расчет_Июнь.xlsx"))
        
        dash._reflow_hist_card(need_vertical=False, lod=3)
        dash._update_kpi_metrics()

        app.processEvents()
        time.sleep(0.1)
        grab_and_save(window, "audit_02_dashboard_filled.png")
    except Exception as e:
        print(f"Error in dash filled: {e}")

    # 3. Norms Tab
    window.switch_page(1)
    app.processEvents()
    time.sleep(0.15)
    grab_and_save(window, "audit_03_norms_page.png")

    # 4. Logs Tab (with mock logs)
    window.switch_page(2)
    try:
        logs_page = window.page_logs
        logs_page.append_log("12:45:01 [INFO] Система инициализирована. Загружен расчетный модуль v2.5", "INFO")
        logs_page.append_log("12:45:02 [SUCCESS] Проверка структуры Excel шаблона: 42 лицевых счета... Успешно", "SUCCESS")
        logs_page.append_log("12:45:02 [WARNING] Предупреждение: Обнаружен ПУ #98412 без показаний за прошлый период (применен норматив)", "WARNING")
        logs_page.append_log("12:45:03 [ERROR] Ошибка валидации строки 142: некорректный формат даты поверки", "ERROR")
        logs_page.append_log("12:45:04 [SUCCESS] Расчет завершен с 1 предупреждением (время обработки: 1.24с)", "SUCCESS")
    except Exception as e:
        print(f"Error in logs: {e}")
    app.processEvents()
    time.sleep(0.15)
    grab_and_save(window, "audit_04_logs_page.png")

    # 5. Auto-tests Tab
    window.switch_page(3)
    app.processEvents()
    time.sleep(0.15)
    grab_and_save(window, "audit_05_tests_page.png")

    # 6. About Page - with waves enabled and sliders
    window.switch_page(4)
    try:
        about = window.page_about
        about.chk_enable_waves.setChecked(True)
        about.sld_density.setValue(35)
        about.sld_opacity.setValue(85)
        about.sld_amp.setValue(120)
        about.sld_speed.setValue(15)
        about.sld_tilt.setValue(45)
    except Exception as e:
        print(f"Error in about: {e}")
    app.processEvents()
    time.sleep(0.25)
    grab_and_save(window, "audit_06_about_page_waves.png")

    # 7. Pearl Light Theme
    try:
        ThemeManager.apply_theme("Pearl Light")
        window.switch_page(0)
        app.processEvents()
        time.sleep(0.2)
        grab_and_save(window, "audit_07_theme_pearl_light.png")
    except Exception as e:
        print(f"Error in pearl light theme test: {e}")

    # 8. Cyberpunk Neon Theme
    try:
        ThemeManager.apply_theme("Cyberpunk Neon")
        window.switch_page(0)
        app.processEvents()
        time.sleep(0.2)
        grab_and_save(window, "audit_08_theme_cyberpunk.png")
    except Exception as e:
        print(f"Error in cyberpunk theme test: {e}")

    # 9. Emerald Cyber Theme
    try:
        ThemeManager.apply_theme("Emerald Cyber")
        window.switch_page(0)
        app.processEvents()
        time.sleep(0.2)
        grab_and_save(window, "audit_09_theme_emerald.png")
    except Exception as e:
        print(f"Error in emerald theme test: {e}")

    # 10. Deep Violet Glass Theme
    try:
        ThemeManager.apply_theme("Deep Violet Glass")
        window.switch_page(0)
        app.processEvents()
        time.sleep(0.2)
        grab_and_save(window, "audit_10_theme_violet.png")
    except Exception as e:
        print(f"Error in deep violet theme test: {e}")

    # 11. Replacement Dialog Modal (Dark Azure)
    ThemeManager.apply_theme("Dark Tech Azure")
    dlg_rep = MeterReplacementDialog(window)
    dlg_rep.show()
    app.processEvents()
    time.sleep(0.15)
    grab_and_save(dlg_rep, "audit_11_dialog_replacement.png")
    dlg_rep.close()

    # 12. Command Palette Modal (Dark Azure)
    dlg_cmd = CommandPaletteDialog(window)
    dlg_cmd.show()
    app.processEvents()
    time.sleep(0.15)
    grab_and_save(dlg_cmd, "audit_12_dialog_command_palette.png")
    dlg_cmd.close()

    # 13. Donate Dialog Modal
    dlg_donate = DonateDialog(window)
    dlg_donate.show()
    app.processEvents()
    time.sleep(0.15)
    grab_and_save(dlg_donate, "audit_13_dialog_donate.png")
    dlg_donate.close()

    # 14. Beach Rest Dialog Modal
    beach_gif = get_about_asset("beach.gif")
    dlg_beach = BeachRestDialog(beach_gif, window)
    dlg_beach.show()
    app.processEvents()
    time.sleep(0.15)
    grab_and_save(dlg_beach, "audit_14_dialog_beach.png")
    dlg_beach.close()

    # 15. Progress Overlay State (Dark Azure)
    window.switch_page(0)
    try:
        overlay = CalculationProgressOverlay(window)
        overlay.resize(window.size())
        overlay.set_step(1)
        overlay.show()
        app.processEvents()
        time.sleep(0.15)
        grab_and_save(window, "audit_15_progress_overlay.png")
        overlay.close()
    except Exception as e:
        print(f"Error in progress overlay: {e}")

    # =========================================================================
    # РЕЖИМ АРКУСА («Как дома» / Windows Classic / 1C Style)
    # =========================================================================
    try:
        ThemeManager.apply_theme("Как дома")
        print("Switching to Arcus Mode ('Как дома')...")

        # 16. Arcus Dashboard - Idle / Reset
        window.switch_page(0)
        dash = window.page_main
        dash.drop_tpl.set_file_path("")
        dash.drop_arc.set_file_path("")
        dash.txt_save.clear()
        dash.txt_cold.clear()
        dash.txt_hot.clear()
        dash.txt_corr.clear()
        dash.table_hist.setRowCount(0)
        dash._reflow_hist_card(need_vertical=False, lod=3)
        dash._update_kpi_metrics()
        app.processEvents()
        time.sleep(0.2)
        grab_and_save(window, "audit_16_arcus_dashboard_idle.png")

        # 17. Arcus Dashboard - Filled Data
        dash.drop_tpl.set_file_path("C:/WaterMetrics/data/Шаблон_Ведомость_2026.xlsx")
        dash.drop_arc.set_file_path("C:/WaterMetrics/data/Экспорт_Аркус_Август.xlsx")
        dash.txt_save.setText("C:/WaterMetrics/output/Результат_Расчета_Август.xlsx")
        dash.txt_cold.setText("1450.50")
        dash.txt_hot.setText("890.20")
        dash.txt_corr.setText("45.00")
        dash.table_hist.setRowCount(3)
        dash.table_hist.setItem(0, 0, QTableWidgetItem("Результат_Расчета_Август_2026.xlsx"))
        dash.table_hist.setItem(0, 1, QTableWidgetItem("C:/WaterMetrics/output/Результат_Расчета_Август_2026.xlsx"))
        dash.table_hist.setItem(1, 0, QTableWidgetItem("Ведомость_Июль_2026_Финальная.xlsx"))
        dash.table_hist.setItem(1, 1, QTableWidgetItem("C:/WaterMetrics/output/Ведомость_Июль_2026_Финальная.xlsx"))
        dash.table_hist.setItem(2, 0, QTableWidgetItem("Тестовый_Расчет_Июнь.xlsx"))
        dash.table_hist.setItem(2, 1, QTableWidgetItem("C:/WaterMetrics/output/Тестовый_Расчет_Июнь.xlsx"))
        dash._reflow_hist_card(need_vertical=False, lod=3)
        dash._update_kpi_metrics()
        app.processEvents()
        time.sleep(0.2)
        grab_and_save(window, "audit_17_arcus_dashboard_filled.png")

        # 18. Arcus Norms Page
        window.switch_page(1)
        app.processEvents()
        time.sleep(0.2)
        grab_and_save(window, "audit_18_arcus_norms_page.png")

        # 19. Arcus Logs Page
        window.switch_page(2)
        app.processEvents()
        time.sleep(0.2)
        grab_and_save(window, "audit_19_arcus_logs_page.png")

        # 20. Arcus Tests Page
        window.switch_page(3)
        app.processEvents()
        time.sleep(0.2)
        grab_and_save(window, "audit_20_arcus_tests_page.png")

        # 21. Arcus About Page
        window.switch_page(4)
        app.processEvents()
        time.sleep(0.2)
        grab_and_save(window, "audit_21_arcus_about_page.png")

        # 22. Arcus Replacement Dialog Modal
        dlg_rep_arc = MeterReplacementDialog(window)
        dlg_rep_arc.show()
        app.processEvents()
        time.sleep(0.15)
        grab_and_save(dlg_rep_arc, "audit_22_arcus_dialog_replacement.png")
        dlg_rep_arc.close()

        # 23. Arcus Command Palette Modal
        dlg_cmd_arc = CommandPaletteDialog(window)
        dlg_cmd_arc.show()
        app.processEvents()
        time.sleep(0.15)
        grab_and_save(dlg_cmd_arc, "audit_23_arcus_dialog_command_palette.png")
        dlg_cmd_arc.close()

        # 24. Arcus Progress Overlay State
        window.switch_page(0)
        overlay_arc = CalculationProgressOverlay(window)
        overlay_arc.resize(window.size())
        overlay_arc.set_step(1)
        overlay_arc.show()
        app.processEvents()
        time.sleep(0.15)
        grab_and_save(window, "audit_24_arcus_progress_overlay.png")
        overlay_arc.close()

    except Exception as e:
        print(f"Error in Arcus Mode captures: {e}")

    print("ALL_AUDIT_CAPTURES_SUCCESS")
    window.close()

if __name__ == "__main__":
    capture_ui()

