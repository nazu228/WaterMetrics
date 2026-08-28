"""
tools/package_release.py
Утилита автоматической сборки релизов WaterMetrics для Яндекс Облака (Object Storage S3).
- Собирает компактный zip-патч без временных файлов и кэша
- Вычисляет SHA-256 хэш
- Генерирует манифест version.json
- Позволяет автоматически загружать файлы в S3 бакет Yandex Cloud
"""

import os
import sys
import json
import zipfile
import hashlib
import argparse
from datetime import datetime, timezone

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Настройка UTF-8 для консоли Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Загрузка переменных из .env при наличии
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip().strip("'\"")
    except Exception:
        pass

from config import APP_VERSION, UPDATE_MANIFEST_URL


def calculate_sha256(filepath: str) -> str:
    """Вычисляет хэш SHA-256 для файла."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest().lower()


def create_patch_zip(version: str, output_zip_path: str) -> int:
    """
    Создает легкий компактный zip-патч (1-2 МБ) только с кодом и ресурсами приложения.
    Исключает бинарники, инсталляторы, тяжелые xlsx файлы, кэш и бэкапы.
    """
    # Разрешенные директории и файлы верхнего уровня
    allowed_dirs = {'core', 'services', 'ui', 'assets'}
    allowed_root_files = {'main.py', 'config.py', 'models.py', 'CHANGELOG.md', 'requirements.txt'}
    exclude_extensions = {'.pyc', '.pyo', '.pyd', '.spec', '.log', '.tmp', '.exe', '.xlsx', '.zip', '.bak'}

    print(f"[*] Упаковка компактного zip-патча v{version} (1-2 МБ)...")
    file_count = 0

    with zipfile.ZipFile(output_zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, files in os.walk(BASE_DIR):
            # Пропускаем кэш и служебные папки
            dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', '.pytest_cache', 'build', 'dist', 'dist_installer', 'dist_release', 'versions', 'backups', '.venv', 'venv') and not d.startswith('.')]

            rel_root = os.path.relpath(root, BASE_DIR)
            top_dir = rel_root.split(os.sep)[0] if rel_root != '.' else '.'

            # Проверяем, разрешена ли текущая директория
            if top_dir != '.' and top_dir not in allowed_dirs:
                continue

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in exclude_extensions or file.startswith('.'):
                    continue

                if top_dir == '.' and file not in allowed_root_files:
                    continue

                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, BASE_DIR)

                zf.write(abs_path, rel_path)
                file_count += 1

    print(f"[OK] Упаковано файлов: {file_count}")
    return file_count


def extract_changelog(version: str) -> str:
    """Извлекает описание изменений для указанной версии из CHANGELOG.md."""
    changelog_file = os.path.join(BASE_DIR, "CHANGELOG.md")
    if not os.path.exists(changelog_file):
        return f"Релиз WaterMetrics v{version}\n- Оптимизация и повышение стабильности."

    try:
        with open(changelog_file, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines()
        capturing = False
        notes = []

        for line in lines:
            if line.startswith("## ") or line.startswith("# "):
                if version in line:
                    capturing = True
                    continue
                elif capturing:
                    break
            elif capturing:
                notes.append(line)

        extracted = "\n".join(notes).strip()
        if extracted:
            return extracted
    except Exception:
        pass

    return f"Релиз WaterMetrics v{version}\n- Улучшения производительности и исправления ошибок."


def upload_to_s3(
    dist_dir: str,
    zip_filename: str,
    bucket_name: str,
    key_id: str,
    secret_key: str
) -> bool:
    """Загружает файлы релиза в Yandex Object Storage через boto3."""
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        print("[!] Ошибка: boto3 не установлен. Установите командой: pip install boto3")
        return False

    print("\n[+] Подключение к Яндекс Облаку (S3)...")
    s3 = boto3.client(
        "s3",
        endpoint_url="https://storage.yandexcloud.net",
        aws_access_key_id=key_id,
        aws_secret_access_key=secret_key
    )

    files_to_upload = [
        (os.path.join(dist_dir, zip_filename), zip_filename, "application/zip"),
        (os.path.join(dist_dir, "version.json"), "version.json", "application/json")
    ]

    for local_path, s3_key, content_type in files_to_upload:
        if not os.path.exists(local_path):
            print(f"[!] Файл не найден: {local_path}")
            continue

        file_size_mb = os.path.getsize(local_path) / (1024 * 1024)
        print(f"[*] Загрузка {s3_key} ({file_size_mb:.2f} МБ) в бакет '{bucket_name}'...")

        try:
            s3.upload_file(
                local_path,
                bucket_name,
                s3_key,
                ExtraArgs={
                    "ContentType": content_type,
                    "ACL": "public-read"
                }
            )
            print(f"[OK] Успешно загружен: {s3_key}")
        except ClientError as e:
            # Если ACL public-read заблокирован настройками бакета, загружаем без ACL
            try:
                s3.upload_file(
                    local_path,
                    bucket_name,
                    s3_key,
                    ExtraArgs={"ContentType": content_type}
                )
                print(f"[OK] Успешно загружен (без явного ACL): {s3_key}")
            except Exception as inner_e:
                print(f"[!] Ошибка загрузки {s3_key}: {inner_e}")
                return False

    print(f"\n[OK] ВСЕ ФАЙЛЫ УСПЕШНО ЗАГРУЖЕНЫ В ЯНДЕКС ОБЛАКО! (Бакет: {bucket_name})")
    return True


def build_release_package(
    bucket_name: str = "watermetrics-releases",
    version: str = APP_VERSION,
    upload: bool = False,
    key_id: str = "",
    secret_key: str = ""
):
    """
    Главная функция сборки релизного пакета.
    """
    dist_dir = os.path.join(BASE_DIR, "dist_release")
    os.makedirs(dist_dir, exist_ok=True)

    zip_filename = f"watermetrics-v{version}.zip"
    zip_filepath = os.path.join(dist_dir, zip_filename)

    # 1. Создаем ZIP-архив
    create_patch_zip(version, zip_filepath)

    # 2. Вычисляем размер и SHA-256
    file_size = os.path.getsize(zip_filepath)
    file_sha256 = calculate_sha256(zip_filepath)
    size_mb = file_size / (1024 * 1024)

    print(f"[*] Архив создан: {zip_filename} ({size_mb:.2f} МБ)")
    print(f"[*] SHA-256 хэш: {file_sha256}")

    # 3. Формируем URL для скачивания
    download_url = f"https://storage.yandexcloud.net/{bucket_name}/{zip_filename}"

    # 4. Формируем манифест version.json
    release_notes = extract_changelog(version)

    manifest_data = {
        "version": version,
        "release_name": f"WaterMetrics v{version}",
        "release_notes": release_notes,
        "published_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "download_url": download_url,
        "sha256": file_sha256,
        "size": file_size,
        "is_patch": True,
        "asset_name": zip_filename
    }

    manifest_path = os.path.join(dist_dir, "version.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] Манифест сгенерирован: {manifest_path}")

    # 5. Автоматическая загрузка, если запрошена
    if upload:
        key = key_id or os.getenv("YC_KEY_ID", "")
        sec = secret_key or os.getenv("YC_SECRET_KEY", "")
        if key and sec:
            upload_to_s3(dist_dir, zip_filename, bucket_name, key, sec)
        else:
            print("\n[!] Ошибка: Для загрузки не указаны ключи YC_KEY_ID и YC_SECRET_KEY.")
    else:
        print("\n" + "=" * 60)
        print("ГОТОВО К ЗАГРУЗКЕ В ЯНДЕКС ОБЛАКО:")
        print("=" * 60)
        print(f"1. Откройте бакет: https://console.yandex.cloud/ -> Object Storage -> '{bucket_name}'")
        print(f"2. Загрузите файлы из папки: {dist_dir}")
        print(f"   - {zip_filename}")
        print(f"   - version.json")
        print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Сборка и публикация релиза для Яндекс Облака")
    parser.add_argument("--version", default=APP_VERSION, help="Номер версии релиза (по умолчанию из config.py)")
    parser.add_argument("--bucket", default=os.getenv("YC_BUCKET", "watermetrics-releases"), help="Имя S3-бакета")
    parser.add_argument("--upload", action="store_true", help="Автоматически загрузить файлы в Яндекс Облако")
    parser.add_argument("--key-id", default="", help="Идентификатор ключа доступа (Key ID)")
    parser.add_argument("--secret-key", default="", help="Секретный ключ доступа (Secret Key)")

    args = parser.parse_args()
    build_release_package(
        bucket_name=args.bucket,
        version=args.version,
        upload=args.upload,
        key_id=args.key_id,
        secret_key=args.secret_key
    )
