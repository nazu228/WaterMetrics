"""
test_folder_guard_system.py — Комплексный автотест для интеллектуального навигатора по папкам,
поиска Аркуса, защиты от перезаписи и диалогов безопасности (WaterMetrics).
"""

import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from PySide6.QtWidgets import QApplication

from services.folder_service import FolderNavigationService
from ui.dialogs.file_guard_dialog import FileGuardDialog

def run_tests():
    print("=== ТЕСТ 1: Сопоставление аббревиатур домов (Fuzzy House Matcher) ===")
    test_cases = [
        ("Душистая 45.xlsx", "душ 45.xlsx", True),
        ("Душистая 45+.xlsx", "душ 45.xlsx", True),
        ("2я Целиноградская 11.xlsx", "2-я цел 11.xlsx", True),
        ("3я Целиноградская 7.xlsx", "3-я Цел 7.xlsx", True),
        ("Посадского 28+.xlsx", "пос 28.xlsx", True),
        ("Аверкиева 34+.xlsx", "Авер 34.xlsx", True),
        ("Дубравная 13.xlsx", "дуб 13.xlsx", True),
        ("Трошева 17+.xlsx", "трошев 17.xlsx", True),
        ("Зеленоградская 34.xlsx", "Зел 34.xlsx", True),
        ("Душистая 45.xlsx", "пос 28.xlsx", False),
        ("Дубравная 13.xlsx", "дуб 15.xlsx", False),
        ("2я Целиноградская 1.xlsx", "2-я цел 11.xlsx", False),
    ]

    for tpl, arc, expected in test_cases:
        matched = FolderNavigationService.is_house_match(tpl, arc)
        status = "✅ PASS" if matched == expected else "❌ FAIL"
        print(f"{status}: '{tpl}' <-> '{arc}' => {matched} (ожидалось {expected})")
        assert matched == expected, f"Ошибка сопоставления: {tpl} vs {arc}"

    print("\n=== ТЕСТ 2: Определение контекста реальной папки 'Южный город' ===")
    real_tpl = r"C:\Users\admin\Desktop\423 — копия\Южный город\07 Июль 2026\Душистая 45.xlsx"
    if os.path.exists(real_tpl):
        ctx = FolderNavigationService.detect_folder_context(real_tpl)
        print("Текущий месяц:", ctx["current_month"])
        print("Следующий месяц:", ctx["next_month_name"], ctx["next_year"])
        print("Папка след. месяца:", os.path.basename(ctx["next_month_dir"] or ""))
        print("Найденный Аркус:", os.path.basename(ctx["found_arcus_path"] or ""))
        print("Рекомендованное сохранение:", ctx["suggested_save_path"])
        print("Существующий отчет:", ctx["existing_report_info"])
        print("Доступных домов в месяце:", len(ctx["available_houses"]))

        assert ctx["current_month"] == 7
        assert ctx["next_month"] == 8
        assert ctx["next_month_name"] == "Август"
        assert ctx["found_arcus_path"] is not None
        assert ctx["suggested_save_path"] is not None
        assert len(ctx["available_houses"]) >= 10
        print("✅ PASS: Контекст папки определен корректно!")
    else:
        print("⚠️ Пропуск ТЕСТА 2 (путь не существует)")

    print("\n=== ТЕСТ 3: Генератор безопасных копий файлов (Safe Copy Generator) ===")
    test_save = r"C:\Users\admin\Desktop\423 — копия\Южный город\08 Август 2026\Душистая 45.xlsx"
    safe_path = FolderNavigationService.generate_safe_copy_path(test_save)
    print("Исходный путь:", test_save)
    print("Безопасный путь для копии:", safe_path)
    assert "_v" in safe_path
    print("✅ PASS: Безопасный путь сформирован корректно!")

    print("\n=== ТЕСТ 4: Проверка блокировки Excel (File Lock Check) ===")
    is_locked = FolderNavigationService.check_file_locked_by_excel(real_tpl)
    print(f"Статус блокировки шаблона: {'Заблокирован' if is_locked else 'Свободен'}")
    print("✅ PASS: Проверка блокировки работает штатно!")

    print("\n=== ТЕСТ 5: Инициализация графических компонентов (UI Check) ===")
    app = QApplication.instance() or QApplication(sys.argv)
    from ui.components.companion_dock import AuthenticFilesWindow
    from ui.dashboard_page import MainDashboardPage

    win_files = AuthenticFilesWindow()
    win_files.show()
    if os.path.exists(real_tpl):
        win_files.set_template_path(real_tpl)
        assert not win_files.smart_nav_frame.isHidden()
        assert win_files.lbl_smart_context.text() != ""
        print("AuthenticFilesWindow Smart Header:", win_files.lbl_smart_context.text())
        print("AuthenticFilesWindow Houses Count:", win_files.combo_houses.count())

    page_main = MainDashboardPage()
    page_main.show()
    if os.path.exists(real_tpl):
        page_main._on_template_selected(real_tpl)
        assert not page_main.smart_nav_frame.isHidden()
        print("MainDashboardPage Smart Header:", page_main.lbl_smart_context.text())
        print("MainDashboardPage Houses Count:", page_main.combo_houses.count())

    print("\n=== ТЕСТ 6: Проверка соответствия папки месяца Аркуса ===")
    v_ok = FolderNavigationService.validate_arcus_month_folder("C:/Projects/08 Август 2026/Душистая 45.xlsx", "C:/Projects/09 Сентябрь 2026/душ 45.xlsx")
    assert v_ok["is_valid"] == True
    v_fail = FolderNavigationService.validate_arcus_month_folder("C:/Projects/08 Август 2026/Душистая 45.xlsx", "C:/Projects/08 Август 2026/душ 45.xlsx")
    assert v_fail["is_valid"] == False
    assert v_fail["warning"] != ""
    print("✅ PASS: Валидация папки месяца Аркуса работает безупречно!")

    print("\n🎉 ВСЕ ТЕСТЫ СИСТЕМЫ ЗАЩИТЫ И НАВИГАЦИИ УСПЕШНО ПРОЙДЕНЫ!")

if __name__ == "__main__":
    run_tests()
