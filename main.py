# main.py
import sys
import os

# Очистка устаревших путей PyInstaller _MEIPASS из sys.path и окружения
if not getattr(sys, 'frozen', False):
    os.environ.pop('_MEIPASS2', None)
    os.environ.pop('_MEIPASS', None)
sys.path = [p for p in sys.path if not ('_MEI' in p and not os.path.exists(p))]

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QSurfaceFormat, QIcon
from config import APP_VERSION
from services.updater_service import VersionManager
from ui.main_window import MainWindow
from ui.styles import DARK_AZURE_QSS

def setup_modular_version_path():
    """Подключает путь к модульной версии кода только в режиме скрипта."""
    is_frozen = getattr(sys, 'frozen', False)
    active_ver = VersionManager.get_active_version()
    if not is_frozen:
        v_dir = os.path.join(VersionManager.get_versions_dir(), f"v{active_ver}")
        if os.path.isdir(v_dir) and v_dir not in sys.path:
            sys.path.insert(0, v_dir)
    return APP_VERSION if is_frozen else active_ver

def get_asset_path(filename: str) -> str:
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, 'assets', filename)

def main():
    active_ver = setup_modular_version_path()
    VersionManager.crash_guard_mark_starting(active_ver)

    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('watermetrics.calculator.app.1.0')
        except Exception:
            pass

    # Установить OpenGL 3.3 Core + MSAA до создания QApplication
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    fmt.setSamples(4)
    QSurfaceFormat.setDefaultFormat(fmt)

    app = QApplication(sys.argv)
    
    icon_path = get_asset_path('app_icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    app.setStyleSheet(DARK_AZURE_QSS)

    window = MainWindow()
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
        
    window.show()

    # Фиксируем успешный запуск в Crash Guard
    VersionManager.crash_guard_mark_success()

    ret = app.exec()
    try:
        window.close()
        del window
        del app
        import gc
        gc.collect()
    except Exception:
        pass

    sys.exit(ret)

if __name__ == "__main__":
    main()

