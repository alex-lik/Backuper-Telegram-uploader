"""Коннектор для S3/R2 хранилищ."""

import os
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError

from .base import BaseConnector


class S3Connector(BaseConnector):
    """Коннектор для S3-совместимых хранилищ (AWS S3, Cloudflare R2)."""

    MAX_FILE_SIZE = None  # Поддерживает multipart upload

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._client = None
        self._resource = None

    @property
    def name(self) -> str:
        return "S3/R2"

    @property
    def type(self) -> str:
        return self.config.get("type", "s3")

    def _get_client(self):
        """Получить S3 клиент."""
        if self._client is None:
            endpoint = self.config.get("endpoint", "")
            access_key = self.config.get("access_key", "")
            secret_key = self.config.get("secret_key", "")
            region = self.config.get("region", "us-east-1")

            if endpoint:
                # Для R2 и других S3-совместимых хранилищ
                self._client = boto3.client(
                    "s3",
                    endpoint_url=endpoint,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region,
                )
            else:
                # Для AWS S3
                self._client = boto3.client(
                    "s3",
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region,
                )

        return self._client

    def _get_resource(self):
        """Получить S3 ресурс."""
        if self._resource is None:
            endpoint = self.config.get("endpoint", "")
            access_key = self.config.get("access_key", "")
            secret_key = self.config.get("secret_key", "")
            region = self.config.get("region", "us-east-1")

            if endpoint:
                self._resource = boto3.resource(
                    "s3",
                    endpoint_url=endpoint,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region,
                )
            else:
                self._resource = boto3.resource(
                    "s3",
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region,
                )

        return self._resource

    def test_connection(self) -> tuple[bool, str]:
        """Проверить подключение к S3."""
        try:
            client = self._get_client()
            bucket = self.config.get("bucket", "")
            client.head_bucket(Bucket=bucket)
            return True, f"S3 подключен: {bucket}"
        except ClientError as e:
            return False, f"Ошибка S3: {e}"
        except Exception as e:
            return False, str(e)

    def upload_file(self, file_path: str, remote_path: str | None = None) -> tuple[bool, str]:
        """Загрузить файл в S3."""
        try:
            client = self._get_client()
            bucket = self.config.get("bucket", "")

            filename = os.path.basename(file_path)
            if remote_path:
                filename = remote_path

            # Для больших файлов используем multipart
            file_size = os.path.getsize(file_path)
            if file_size > 100 * 1024 * 1024:  # > 100MB
                return self._upload_multipart(file_path, bucket, filename)

            client.upload_file(file_path, bucket, filename)
            return True, f"s3://{bucket}/{filename}"
        except Exception as e:
            return False, str(e)

    def _upload_multipart(self, file_path: str, bucket: str, key: str) -> tuple[bool, str]:
        """Загрузить файл с помощью multipart upload."""
        client = self._get_client()

        try:
            # Создаем multipart upload
            response = client.create_multipart_upload(Bucket=bucket, Key=key)
            upload_id = response["UploadId"]

            parts = []
            part_number = 1
            file_size = os.path.getsize(file_path)
            chunk_size = 100 * 1024 * 1024  # 100MB

            with open(file_path, "rb") as f:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break

                    result = client.upload_part(
                        Body=data,
                        Bucket=bucket,
                        Key=key,
                        UploadId=upload_id,
                        PartNumber=part_number,
                    )
                    parts.append({"ETag": result["ETag"], "PartNumber": part_number})
                    part_number += 1

            # Завершаем multipart upload
            client.complete_multipart_upload(
                Bucket=bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )

            return True, f"s3://{bucket}/{key}"
        except Exception:
            # Отменяем upload при ошибке
            try:
                client.abort_multipart_upload(Bucket=bucket, Key=key, UploadId=upload_id)
            except Exception:
                pass
            raise

    def upload_data(self, data: bytes, remote_name: str) -> tuple[bool, str]:
        """Загрузить данные в S3."""
        try:
            client = self._get_client()
            bucket = self.config.get("bucket", "")

            client.put_object(Body=data, Bucket=bucket, Key=remote_name)
            return True, f"s3://{bucket}/{remote_name}"
        except Exception as e:
            return False, str(e)

    def download_file(self, key: str) -> bytes | None:
        """Скачать файл из S3."""
        try:
            client = self._get_client()
            bucket = self.config.get("bucket", "")
            response = client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()
        except Exception:
            return None

    def close(self):
        """Закрыть соединение."""
        self._client = None
        self._resource = None
