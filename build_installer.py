"""
build_installer.py
Скрипт автоматизированной сборки исполняемого файла PyInstaller и Windows-инсталлятора Inno Setup.
"""

import os
import sys
import subprocess
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(ROOT_DIR, "dist")
ISS_SCRIPT = os.path.join(ROOT_DIR, "installer", "setup_script.iss")


def find_inno_setup_compiler() -> str:
    """Поиск компилятора Inno Setup (iscc.exe) в стандартных путях Windows."""
    paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
        shutil.which("iscc") or "",
        shutil.which("ISCC.exe") or ""
    ]
    for p in paths:
        if p and os.path.exists(p):
            return p
    return ""


def build_pyinstaller():
    print("=" * 60)
    print("1. Сборка исполняемого файла WaterMetrics.exe через PyInstaller...")
    print("=" * 60)
    cmd = [sys.executable, "-m", "PyInstaller", "WaterMetrics.spec", "--noconfirm"]
    res = subprocess.run(cmd, cwd=ROOT_DIR)
    if res.returncode != 0:
        print("[ERROR] Ошибка при сборке PyInstaller.")
        sys.exit(1)
    print("[OK] WaterMetrics.exe успешно собран в папке dist/!")


def build_inno_setup():
    print("=" * 60)
    print("2. Сборка инсталлятора WaterMetrics_Setup_v1.0.exe...")
    print("=" * 60)
    iscc = find_inno_setup_compiler()
    if not iscc:
        print("[WARNING] Inno Setup (ISCC.exe) не найден в стандартных путях.")
        print("          Для локальной сборки инсталлятора установите Inno Setup 6 (https://jrsoftware.org/isdl.php).")
        print("          В GitHub Actions сборка инсталлятора выполнится автоматически!")
        return

    cmd = [iscc, ISS_SCRIPT]
    res = subprocess.run(cmd, cwd=ROOT_DIR)
    if res.returncode != 0:
        print("[ERROR] Ошибка при компиляции Inno Setup.")
        sys.exit(1)
    print("[OK] Инсталлятор WaterMetrics_Setup_v1.0.exe успешно создан в dist/!")


if __name__ == "__main__":
    build_pyinstaller()
    build_inno_setup()
