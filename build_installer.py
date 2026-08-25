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
    from config import APP_VERSION
    print("=" * 60)
    print(f"2. Сборка инсталлятора WaterMetrics_Setup_v{APP_VERSION}.exe...")
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
    print(f"[OK] Инсталлятор WaterMetrics_Setup_v{APP_VERSION}.exe успешно создан в dist/!")


def build_patch_archive():
    import zipfile
    from config import APP_VERSION
    print("=" * 60)
    print(f"3. Создание легковесного zip-патча v{APP_VERSION} (1-2 МБ)...")
    print("=" * 60)
    os.makedirs(DIST_DIR, exist_ok=True)
    patch_zip_path = os.path.join(DIST_DIR, f"WaterMetrics_v{APP_VERSION}_patch.zip")
    
    ignored_dirs = {'__pycache__', '.git', 'build', 'dist', '.vscode', '.idea', '.gemini', 'env', 'venv', '.venv'}
    ignored_exts = {'.pyc', '.pyo', '.tmp', '.bak', '.swp', '.swo'}

    with zipfile.ZipFile(patch_zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(ROOT_DIR):
            dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.startswith('.')]
            for f in files:
                if any(f.endswith(ext) for ext in ignored_exts) or f in {'Thumbs.db', 'Desktop.ini', '.DS_Store'}:
                    continue
                full_p = os.path.join(root, f)
                rel_p = os.path.relpath(full_p, ROOT_DIR)
                z.write(full_p, rel_p)
                
    size_mb = os.path.getsize(patch_zip_path) / (1024 * 1024)
    print(f"[OK] Zip-патч успешно создан: {patch_zip_path} ({size_mb:.2f} МБ)!")


if __name__ == "__main__":
    build_pyinstaller()
    build_inno_setup()
    build_patch_archive()
    print("\n🎉 Все артефакты сборки готовы в папке dist/!")
