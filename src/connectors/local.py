"""Коннектор для локальной папки."""

import os
import shutil
from pathlib import Path
from typing import Any

from .base import BaseConnector


class LocalConnector(BaseConnector):
    """Коннектор для копирования файлов в локальную папку."""

    MAX_FILE_SIZE = None  # Без ограничений

    @property
    def name(self) -> str:
        return "Локальная папка"

    @property
    def type(self) -> str:
        return "local"

    def test_connection(self) -> tuple[bool, str]:
        """Проверить доступность папки."""
        path = self.config.get("local_path", "")
        if not path:
            return False, "Путь не указан"
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
                return True, f"Папка создана: {path}"
            except Exception as e:
                return False, f"Ошибка создания: {e}"
        if not os.path.isdir(path):
            return False, "Указанный путь не является папкой"
        return True, f"Папка доступна: {path}"

    def upload_file(self, file_path: str, remote_path: str | None = None) -> tuple[bool, str]:
        """Скопировать файл в целевую папку."""
        target_dir = self.config.get("local_path", "")
        if not target_dir:
            return False, "Путь не настроен"

        Path(target_dir).mkdir(parents=True, exist_ok=True)

        filename = os.path.basename(file_path)
        if remote_path:
            filename = remote_path

        target_path = os.path.join(target_dir, filename)

        try:
            if os.path.isdir(file_path):
                shutil.copytree(file_path, target_path)
            else:
                shutil.copy2(file_path, target_path)
            return True, target_path
        except Exception as e:
            return False, str(e)

    def upload_data(self, data: bytes, remote_name: str) -> tuple[bool, str]:
        """Записать данные в файл."""
        target_dir = self.config.get("local_path", "")
        if not target_dir:
            return False, "Путь не настроен"

        Path(target_dir).mkdir(parents=True, exist_ok=True)

        target_path = os.path.join(target_dir, remote_name)

        try:
            with open(target_path, "wb") as f:
                f.write(data)
            return True, target_path
        except Exception as e:
            return False, str(e)
