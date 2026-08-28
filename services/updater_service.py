"""
services/updater_service.py
Модуль удаленных обновлений WaterMetrics:
- Поддержка Яндекс Облака (S3 / Serverless Manifest) и GitHub Releases (fallback).
- Криптографическая проверка целостности файлов (SHA-256).
- Генерация HWID для будущей системы лицензирования.
- Асинхронное скачивание с индикацией прогресса.
- Crash-Guard и безопасная установка на Windows.
"""

import os
import sys
import json
import re
import hashlib
import platform
import uuid
import tempfile
import subprocess
import urllib.request
import urllib.error
import ssl
from typing import Optional, Tuple, List
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal, QObject, QSettings
from config import (
    APP_VERSION, DEFAULT_GITHUB_REPO, GITHUB_API_BASE,
    UPDATE_MANIFEST_URL, LICENSE_API_URL, DATA_DIR
)


def calculate_file_sha256(file_path: str) -> str:
    """Вычисляет SHA-256 хэш локального файла."""
    if not os.path.isfile(file_path):
        return ""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest().lower()


def verify_file_sha256(file_path: str, expected_hash: str) -> bool:
    """Проверяет соответствие SHA-256 хэша файла эталону."""
    if not expected_hash:
        return True  # Если хэш не передан, проверка пропускается
    actual = calculate_file_sha256(file_path)
    return actual == expected_hash.strip().lower()


def get_system_hwid() -> str:
    """
    Генерирует стабильный анонимизированный идентификатор оборудования (HWID)
    для привязки лицензий (Windows).
    """
    components = []
    # 1. UUID материнской платы / системы через WMIC / PowerShell (Windows)
    if sys.platform == 'win32':
        try:
            cmd = "powershell -Command \"(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID\""
            out = subprocess.check_output(cmd, shell=True, text=True, timeout=2).strip()
            if out:
                components.append(out)
        except Exception:
            pass

    # 2. Сетевой MAC + имя узла + архитектура
    try:
        node = str(uuid.getnode())
        machine = platform.machine()
        processor = platform.processor()
        components.append(f"{node}_{machine}_{processor}")
    except Exception:
        pass

    raw_id = "::".join(components) or f"fallback_{platform.node()}"
    return hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:32].upper()


def parse_version(version_str: str) -> Tuple[int, ...]:
    """
    Преобразует строку версии (например 'v2.6.0', '2.6.1-patch', 'v3.0') в кортеж чисел.
    """
    if not version_str:
        return (0, 0, 0)
    
    clean = version_str.strip().lstrip('vV')
    main_part = clean.split('-')[0].split('+')[0]
    tokens = re.findall(r'\d+', main_part)
    if not tokens:
        return (0, 0, 0)
    return tuple(int(t) for t in tokens)


def is_newer_version(current_ver: str, remote_ver: str) -> bool:
    """
    Проверяет, является ли remote_ver более новой, чем current_ver.
    """
    curr = parse_version(current_ver)
    rem = parse_version(remote_ver)
    
    max_len = max(len(curr), len(rem), 3)
    curr_pad = curr + (0,) * (max_len - len(curr))
    rem_pad = rem + (0,) * (max_len - len(rem))
    
    return rem_pad > curr_pad


class VersionManager:
    """
    Менеджер версий кодовой базы, безопасного отката и Crash-Guard системы.
    Позволяет хранить прошлые версии и обновляться легкими патчами (1-2 МБ).
    """
    VERSIONS_DIR = os.path.join(DATA_DIR, "versions")
    MAX_STORED_VERSIONS = 3

    @classmethod
    def get_versions_dir(cls) -> str:
        os.makedirs(cls.VERSIONS_DIR, exist_ok=True)
        return cls.VERSIONS_DIR

    @classmethod
    def get_installed_versions(cls) -> List[str]:
        """Возвращает список установленных локальных версий, отсортированных по убыванию."""
        v_dir = cls.get_versions_dir()
        versions = [APP_VERSION]
        if os.path.exists(v_dir):
            for d in os.listdir(v_dir):
                d_path = os.path.join(v_dir, d)
                if os.path.isdir(d_path) and (d.startswith("v") or d[0].isdigit()):
                    v_str = d.lstrip("vV")
                    if v_str not in versions:
                        versions.append(v_str)

        versions.sort(key=lambda v: parse_version(v), reverse=True)
        return versions

    @classmethod
    def get_active_version(cls) -> str:
        settings = QSettings("WaterMetrics", "VersionControl")
        return settings.value("ActiveVersion", APP_VERSION, type=str)

    @classmethod
    def set_active_version(cls, version_str: str):
        settings = QSettings("WaterMetrics", "VersionControl")
        clean_v = version_str.lstrip("vV")
        settings.setValue("ActiveVersion", clean_v)

    @classmethod
    def install_patch(cls, zip_path: str, version_str: str) -> bool:
        """Распаковывает легкий zip-патч в папку новой версии и активирует ее."""
        import zipfile
        import shutil
        try:
            clean_v = version_str.lstrip("vV")
            target_dir = os.path.join(cls.get_versions_dir(), f"v{clean_v}")
            os.makedirs(target_dir, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(target_dir)

            entries = [e for e in os.listdir(target_dir) if not e.startswith('.')]
            if len(entries) == 1:
                single_sub = os.path.join(target_dir, entries[0])
                if os.path.isdir(single_sub):
                    for item in os.listdir(single_sub):
                        dst = os.path.join(target_dir, item)
                        if os.path.exists(dst):
                            if os.path.isdir(dst):
                                shutil.rmtree(dst, ignore_errors=True)
                            else:
                                os.remove(dst)
                        shutil.move(os.path.join(single_sub, item), dst)
                    try:
                        shutil.rmtree(single_sub, ignore_errors=True)
                    except Exception:
                        pass

            cls.set_active_version(clean_v)
            cls.cleanup_old_versions()
            return True
        except Exception as e:
            print(f"[VersionManager] Ошибка установки патча: {e}")
            return False

    @classmethod
    def cleanup_old_versions(cls):
        """Удаляет старые версии, оставляя только последние MAX_STORED_VERSIONS."""
        import shutil
        installed = cls.get_installed_versions()
        active = cls.get_active_version()
        to_keep = set(installed[:cls.MAX_STORED_VERSIONS])
        to_keep.add(active)
        to_keep.add(APP_VERSION)

        v_dir = cls.get_versions_dir()
        if os.path.exists(v_dir):
            for d in os.listdir(v_dir):
                d_clean = d.lstrip("vV")
                if d_clean not in to_keep:
                    full_p = os.path.join(v_dir, d)
                    try:
                        shutil.rmtree(full_p, ignore_errors=True)
                    except Exception:
                        pass

    @classmethod
    def rollback_to_previous_version(cls) -> Optional[str]:
        """Откатывает активную версию на предыдущую стабильную."""
        installed = cls.get_installed_versions()
        current = cls.get_active_version()

        try:
            idx = installed.index(current)
            if idx + 1 < len(installed):
                fallback = installed[idx + 1]
                cls.set_active_version(fallback)
                return fallback
        except ValueError:
            pass

        if installed:
            fallback = installed[-1]
            cls.set_active_version(fallback)
            return fallback
        return None

    @classmethod
    def crash_guard_mark_starting(cls, version_str: str):
        """Фиксирует начало запуска версии."""
        settings = QSettings("WaterMetrics", "CrashGuard")
        settings.setValue("Status", "STARTING")
        settings.setValue("Version", version_str.lstrip("vV"))

    @classmethod
    def crash_guard_mark_success(cls):
        """Фиксирует успешный старт программы (окно открыто)."""
        settings = QSettings("WaterMetrics", "CrashGuard")
        settings.setValue("Status", "SUCCESS")

    @classmethod
    def crash_guard_check_crashed(cls) -> Optional[Tuple[str, str]]:
        """
        Проверяет, не упал ли прошлый запуск.
        Если упал — автоматически откатывает на предыдущую версию.
        Возвращает (failed_version, fallback_version) или None.
        """
        settings = QSettings("WaterMetrics", "CrashGuard")
        status = settings.value("Status", "SUCCESS", type=str)
        crashed_ver = settings.value("Version", APP_VERSION, type=str)

        if status == "STARTING":
            fallback = cls.rollback_to_previous_version()
            settings.setValue("Status", "RECOVERED")
            return (crashed_ver, fallback or APP_VERSION)
        return None


@dataclass
class ReleaseInfo:
    """Универсальная модель метаданных релиза."""
    tag_name: str
    version: str
    name: str
    body: str
    published_at: str
    html_url: str
    asset_name: Optional[str] = None
    asset_download_url: Optional[str] = None
    asset_size: int = 0
    is_patch: bool = False
    sha256: str = ""

    @property
    def download_url(self) -> Optional[str]:
        return self.asset_download_url


# Алиас для обратной совместимости
GitHubReleaseInfo = ReleaseInfo


class RemoteUpdateChecker(QThread):
    """
    Асинхронный воркер проверки обновлений.
    Поддерживает:
    1. Яндекс Облако (S3-манифест version.json или Serverless API)
    2. Fallback на GitHub Releases при отсутствии S3-манифеста
    """
    update_available = Signal(object)      # ReleaseInfo
    already_latest = Signal(str)          # current_version
    check_failed = Signal(str)            # error_message

    def __init__(
        self,
        manifest_url: Optional[str] = None,
        repo: str = DEFAULT_GITHUB_REPO,
        current_ver: str = APP_VERSION,
        license_key: Optional[str] = None,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self.manifest_url = manifest_url or UPDATE_MANIFEST_URL
        self.repo = repo.strip()
        self.current_ver = current_ver
        self.license_key = license_key
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            # ── 1. Пробуем проверить через Яндекс Облако (S3 / Serverless manifest) ──
            if self.manifest_url:
                try:
                    info = self._check_yandex_manifest()
                    if info:
                        if self._is_cancelled:
                            return
                        if is_newer_version(self.current_ver, info.version):
                            self.update_available.emit(info)
                        else:
                            self.already_latest.emit(self.current_ver)
                        return
                except Exception as s3_err:
                    # Если манифест S3 недоступен (например, еще не залит), пробуем fallback
                    print(f"[Updater] S3-манифест не ответил ({s3_err}), пробуем GitHub...")

            # ── 2. Fallback: GitHub Releases ──
            if self.repo and "/" in self.repo:
                info = self._check_github_releases()
                if self._is_cancelled:
                    return
                if info and is_newer_version(self.current_ver, info.version):
                    self.update_available.emit(info)
                elif info:
                    self.already_latest.emit(self.current_ver)
            else:
                self.check_failed.emit("Не настроен источник обновлений (манифест или репозиторий).")

        except urllib.error.HTTPError as e:
            if e.code == 404:
                self.check_failed.emit("Файл обновлений не найден (404).")
            elif e.code == 403:
                self.check_failed.emit("Доступ к серверу обновлений ограничен (403).")
            else:
                self.check_failed.emit(f"Ошибка сервера обновлений: HTTP {e.code}")
        except urllib.error.URLError as e:
            self.check_failed.emit(f"Не удалось подключиться к серверу обновлений: {e.reason}")
        except Exception as e:
            self.check_failed.emit(f"Ошибка при проверке обновлений: {str(e)}")

    def _check_yandex_manifest(self) -> Optional[ReleaseInfo]:
        """Парсит легковесный JSON-манифест из Яндекс Облака."""
        ctx = ssl.create_default_context()
        headers = {
            "User-Agent": f"WaterMetrics-App/{self.current_ver}",
            "Accept": "application/json"
        }
        if self.license_key:
            headers["X-License-Key"] = self.license_key
            headers["X-HWID"] = get_system_hwid()

        req = urllib.request.Request(self.manifest_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5.0, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))

        remote_ver = str(data.get("version", "")).lstrip("vV")
        if not remote_ver:
            return None

        # Определяем подходящий URL для текущего окружения
        is_frozen = getattr(sys, 'frozen', False)
        download_url = data.get("download_url") or data.get("exe_url" if is_frozen else "patch_url", "")
        asset_name = data.get("asset_name") or ("WaterMetrics_Update.exe" if is_frozen else "WaterMetrics_patch.zip")
        is_patch = bool(data.get("is_patch", not is_frozen))

        return ReleaseInfo(
            tag_name=f"v{remote_ver}",
            version=remote_ver,
            name=data.get("release_name", f"WaterMetrics v{remote_ver}"),
            body=data.get("release_notes", data.get("body", "")),
            published_at=data.get("published_at", ""),
            html_url=data.get("html_url", ""),
            asset_name=asset_name,
            asset_download_url=download_url,
            asset_size=data.get("size", 0),
            is_patch=is_patch,
            sha256=data.get("sha256", "")
        )

    def _check_github_releases(self) -> Optional[ReleaseInfo]:
        """Fallback: чтение релизов через GitHub API."""
        api_url = f"{GITHUB_API_BASE}/{self.repo}/releases/latest"
        req = urllib.request.Request(
            api_url,
            headers={
                "User-Agent": f"WaterMetrics-App/{self.current_ver}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=7.0, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))

        tag_name = data.get("tag_name", "")
        release_name = data.get("name", tag_name)
        body = data.get("body", "")
        published_at = data.get("published_at", "")
        html_url = data.get("html_url", f"https://github.com/{self.repo}/releases")
        assets = data.get("assets", [])

        chosen_asset_name = None
        chosen_download_url = None
        chosen_size = 0
        is_patch = False
        is_frozen = getattr(sys, 'frozen', False)

        if is_frozen:
            for asset in assets:
                name = asset.get("name", "")
                if name.lower().endswith(".exe"):
                    chosen_asset_name = name
                    chosen_download_url = asset.get("browser_download_url")
                    chosen_size = asset.get("size", 0)
                    break
        else:
            for asset in assets:
                name = asset.get("name", "")
                if "patch" in name.lower() and name.lower().endswith(".zip"):
                    chosen_asset_name = name
                    chosen_download_url = asset.get("browser_download_url")
                    chosen_size = asset.get("size", 0)
                    is_patch = True
                    break

        if not chosen_download_url:
            for asset in assets:
                name = asset.get("name", "")
                if name.lower().endswith(".zip"):
                    chosen_asset_name = name
                    chosen_download_url = asset.get("browser_download_url")
                    chosen_size = asset.get("size", 0)
                    is_patch = True
                    break

        if not chosen_download_url:
            chosen_download_url = data.get("zipball_url") or f"https://github.com/{self.repo}/archive/refs/tags/{tag_name}.zip"
            chosen_asset_name = f"WaterMetrics_{tag_name}.zip"
            is_patch = True

        return ReleaseInfo(
            tag_name=tag_name,
            version=tag_name.lstrip('vV'),
            name=release_name,
            body=body,
            published_at=published_at,
            html_url=html_url,
            asset_name=chosen_asset_name,
            asset_download_url=chosen_download_url,
            asset_size=chosen_size,
            is_patch=is_patch,
            sha256=""
        )


# Алиас для обратной совместимости
GitHubUpdateChecker = RemoteUpdateChecker


class RemoteAssetDownloader(QThread):
    """
    Асинхронный воркер потокового скачивания файла обновления с проверкой SHA-256.
    """
    progress = Signal(int, int, int)       # percent (0-100), bytes_downloaded, total_bytes
    finished = Signal(str)                 # local_temp_file_path
    failed = Signal(str)                   # error_message

    def __init__(
        self,
        download_url: str,
        filename: str = "WaterMetrics_update.exe",
        expected_sha256: str = "",
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self.download_url = download_url
        self.filename = filename
        self.expected_sha256 = expected_sha256.strip().lower()
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        temp_file_path = ""
        try:
            temp_dir = os.path.join(tempfile.gettempdir(), "watermetrics_updater")
            os.makedirs(temp_dir, exist_ok=True)
            temp_file_path = os.path.join(temp_dir, self.filename)

            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": f"WaterMetrics-App/{APP_VERSION}"}
            )

            ctx = ssl.create_default_context()

            with urllib.request.urlopen(req, timeout=30.0, context=ctx) as response:
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                chunk_size = 64 * 1024  # 64 KB chunks

                with open(temp_file_path, "wb") as f:
                    while True:
                        if self._is_cancelled:
                            f.close()
                            if os.path.exists(temp_file_path):
                                os.remove(temp_file_path)
                            return

                        chunk = response.read(chunk_size)
                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)

                        pct = int((downloaded / total_size) * 100) if total_size > 0 else 0
                        self.progress.emit(pct, downloaded, total_size)

            if self._is_cancelled:
                return

            # Проверка криптографической целостности (SHA-256)
            if self.expected_sha256:
                if not verify_file_sha256(temp_file_path, self.expected_sha256):
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    self.failed.emit("Нарушена целостность файла обновления (не совпадает контрольная сумма SHA-256).")
                    return

            self.finished.emit(temp_file_path)

        except Exception as e:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception:
                    pass
            self.failed.emit(f"Ошибка загрузки: {str(e)}")


# Алиас для обратной совместимости
GitHubAssetDownloader = RemoteAssetDownloader


class WindowsUpdateDeployer:
    """
    Утилита для развертывания и безопасной замены исполняемого файла на Windows.
    """

    @staticmethod
    def apply_update(downloaded_file: str, version_str: str = "") -> bool:
        """
        Применяет обновление (легкий zip-патч или полный бинарник/инсталлятор) и перезапускает программу.
        """
        try:
            is_frozen = getattr(sys, 'frozen', False)
            current_exe = sys.executable if is_frozen else os.path.abspath(sys.argv[0])
            current_pid = os.getpid()

            # 1. ОБРАБОТКА ЛЕГКОГО ZIP-ПАТЧА (~1.5 МБ)
            if downloaded_file.lower().endswith(".zip"):
                ok = VersionManager.install_patch(downloaded_file, version_str or APP_VERSION)
                if not ok:
                    return False

                # В режиме исходного кода (Python) копируем файлы в рабочую директорию
                if not is_frozen:
                    import shutil
                    clean_v = (version_str or APP_VERSION).lstrip("vV")
                    target_dir = os.path.join(VersionManager.get_versions_dir(), f"v{clean_v}")
                    if os.path.exists(target_dir):
                        root_app_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
                        for item in os.listdir(target_dir):
                            src_item = os.path.join(target_dir, item)
                            dst_item = os.path.join(root_app_dir, item)
                            if os.path.isdir(src_item) and item not in ('.git', '__pycache__', '.pytest_cache', 'versions'):
                                shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
                            elif os.path.isfile(src_item):
                                shutil.copy2(src_item, dst_item)

                # Перезапуск программы с новой версией
                if is_frozen:
                    subprocess.Popen([current_exe], close_fds=True)
                else:
                    subprocess.Popen([sys.executable, current_exe], close_fds=True)
                return True

            # 2. Если скачан установочный exe (installer), запускаем его через ShellExecute (explorer.exe)
            if "setup" in os.path.basename(downloaded_file).lower() or "install" in os.path.basename(downloaded_file).lower():
                if sys.platform == 'win32':
                    try:
                        os.startfile(downloaded_file)
                    except Exception:
                        subprocess.Popen([downloaded_file], creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP, close_fds=True)
                else:
                    subprocess.Popen([downloaded_file])
                return True

            if not is_frozen:
                # В режиме исходного кода (Python)
                return True

            # 3. В режиме прямого .exe бинарника генерируем bat-скрипт замены
            temp_dir = tempfile.gettempdir()
            bat_path = os.path.join(temp_dir, "watermetrics_apply_update.bat")

            bat_content = f"""@echo off
chcp 65001 > nul
echo Ожидание завершения WaterMetrics (PID: {current_pid})...
:wait_loop
tasklist /FI "PID eq {current_pid}" 2>NUL | find /I "{current_pid}" >NUL
if not errorlevel 1 (
    timeout /t 1 /nobreak > nul
    goto wait_loop
)

timeout /t 1 /nobreak > nul
echo Замена файла программы...
copy /Y "{downloaded_file}" "{current_exe}" > nul

echo Запуск обновленного WaterMetrics...
start "" "{current_exe}"

del "{downloaded_file}" > nul 2>&1
del "%~f0" > nul 2>&1
exit
"""
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(bat_content)

            # Запускаем автономный bat-процесс без привязки к текущему
            creation_flags = 0
            if sys.platform == 'win32':
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | 0x08000000  # CREATE_NO_WINDOW

            subprocess.Popen(["cmd.exe", "/c", bat_path], creationflags=creation_flags, close_fds=True)
            return True

        except Exception as e:
            print(f"[UpdateDeployer] Ошибка развертывания: {e}")
            return False
