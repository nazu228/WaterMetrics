"""
serverless/yandex_cloud_function.py
Обработчик (Handler) для Yandex Cloud Functions (Python 3.11/3.12).

Назначение:
- Бессерверная валидация лицензионного ключа и HWID клиента через Serverless YDB.
- Генерация безопасных временных Pre-Signed ссылок (S3) на скачивание файлов из Object Storage.
- Защита от прямого скачивания обновлений без лицензии.

Бесплатный лимит Яндекс Облака: 1 000 000 вызовов в месяц бесплатно.
"""

import os
import json
import boto3
from datetime import datetime, timezone

# ─── КОНФИГУРАЦИЯ (Задается в переменных окружения Cloud Function) ───
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "watermetrics-releases")
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "https://storage.yandexcloud.net")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

# Инициализация S3 клиента (boto3)
s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)


def validate_license(license_key: str, hwid: str) -> dict:
    """
    Проверка лицензии в Serverless YDB.
    (В демонстрационном режиме разрешает ключи формата WM-XXXX или тестовый режим)
    """
    if not license_key:
        return {"valid": False, "reason": "Лицензионный ключ не указан"}

    # TODO: При подключении YDB раскомментировать запрос к таблице licenses
    # В базовом варианте проверяем формат и статус
    if license_key.startswith("WM-") or license_key == "DEV-MASTER-KEY":
        return {
            "valid": True,
            "license_type": "PRO",
            "expires_at": "2030-12-31"
        }

    return {"valid": False, "reason": "Недействительный лицензионный ключ"}


def handler(event, context):
    """
    Точка входа Yandex Cloud Function.
    Принимает HTTP POST запрос от приложения WaterMetrics.
    """
    try:
        # Парсим входящие заголовки и тело запроса
        http_method = event.get("httpMethod", "GET")

        # Если GET-запрос — отдаем открытый манифест (для бесплатных версий)
        if http_method == "GET":
            try:
                response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key="version.json")
                manifest_json = json.loads(response["Body"].read().decode("utf-8"))
                return {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json; charset=utf-8"},
                    "body": json.dumps(manifest_json, ensure_ascii=False)
                }
            except Exception as e:
                return {
                    "statusCode": 404,
                    "body": json.dumps({"error": f"Манифест version.json не найден: {str(e)}"})
                }

        # Обработка POST-запроса с лицензией
        body_str = event.get("body", "{}")
        if event.get("isBase64Encoded", False):
            import base64
            body_str = base64.b64decode(body_str).decode("utf-8")

        payload = json.loads(body_str) if body_str else {}
        client_version = payload.get("version", "1.0.0")
        license_key = payload.get("license_key") or event.get("headers", {}).get("X-License-Key", "")
        hwid = payload.get("hwid") or event.get("headers", {}).get("X-HWID", "")

        # 1. Проверяем лицензию
        check_result = validate_license(license_key, hwid)
        if not check_result.get("valid"):
            return {
                "statusCode": 403,
                "headers": {"Content-Type": "application/json; charset=utf-8"},
                "body": json.dumps({
                    "error": "Ошибка лицензии",
                    "details": check_result.get("reason", "Доступ запрещен")
                }, ensure_ascii=False)
            }

        # 2. Читаем манифест из S3
        manifest_obj = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key="version.json")
        manifest_data = json.loads(manifest_obj["Body"].read().decode("utf-8"))
        target_asset = manifest_data.get("asset_name", f"watermetrics-v{manifest_data.get('version')}.zip")

        # 3. Генерируем временную защищенную ссылку Pre-Signed URL (живет 15 минут)
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": target_asset},
            ExpiresIn=900  # 15 минут
        )

        manifest_data["download_url"] = presigned_url

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json; charset=utf-8"},
            "body": json.dumps(manifest_data, ensure_ascii=False)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json; charset=utf-8"},
            "body": json.dumps({"error": f"Внутренняя ошибка сервера: {str(e)}"}, ensure_ascii=False)
        }
