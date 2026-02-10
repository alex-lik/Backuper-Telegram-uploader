"""Коннектор для Google Drive."""

import os
from pathlib import Path
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from .base import BaseConnector


class GoogleDriveConnector(BaseConnector):
    """Коннектор для Google Drive."""

    MAX_FILE_SIZE = 15 * 1024**3  # 15 GB per account

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._service = None

    @property
    def name(self) -> str:
        return "Google Drive"

    @property
    def type(self) -> str:
        return "google_drive"

    def _get_service(self):
        """Получить Google Drive API сервис."""
        if self._service is None:
            credentials_path = self.config.get("credentials_path", "")
            if not credentials_path:
                raise ValueError("Путь к файлу credentials не указан")

            scopes = ["https://www.googleapis.com/auth/drive.file"]
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=scopes
            )

            self._service = build("drive", "v3", credentials=credentials)

        return self._service

    def test_connection(self) -> tuple[bool, str]:
        """Проверить подключение к Google Drive."""
        try:
            service = self._get_service()
            about = service.about().get(fields="user").execute()
            return True, f"Google Drive подключен: {about.get('user', {}).get('emailAddress', 'unknown')}"
        except Exception as e:
            return False, f"Ошибка Google Drive: {e}"

    def upload_file(self, file_path: str, remote_path: str | None = None) -> tuple[bool, str]:
        """Загрузить файл в Google Drive."""
        try:
            service = self._get_service()
            filename = os.path.basename(file_path)

            # Получаем ID папки
            folder_id = self.config.get("folder_id", "")

            file_metadata = {"name": filename}
            if folder_id:
                file_metadata["parents"] = [folder_id]

            media = MediaFileUpload(file_path, resumable=True)

            file = service.files().create(body=file_metadata, media_body=media, fields="id,webViewLink").execute()
            return True, f"file_{file.get('id')}"
        except HttpError as e:
            return False, f"Ошибка Google Drive: {e}"
        except Exception as e:
            return False, str(e)

    def upload_data(self, data: bytes, remote_name: str) -> tuple[bool, str]:
        """Загрузить данные в Google Drive."""
        try:
            service = self._get_service()
            folder_id = self.config.get("folder_id", "")

            file_metadata = {"name": remote_name}
            if folder_id:
                file_metadata["parents"] = [folder_id]

            # Сохраняем во временный файл
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name

            try:
                media = MediaFileUpload(tmp_path, resumable=True)
                file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
                return True, f"file_{file.get('id')}"
            finally:
                os.unlink(tmp_path)

        except HttpError as e:
            return False, f"Ошибка Google Drive: {e}"
        except Exception as e:
            return False, str(e)

    def close(self):
        """Закрыть соединение."""
        self._service = None
