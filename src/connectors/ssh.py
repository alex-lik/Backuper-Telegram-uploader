"""Коннектор для SSH/SCP."""

import os
import paramiko
from pathlib import Path
from typing import Any

from .base import BaseConnector


class SSHConnector(BaseConnector):
    """Коннектор для загрузки файлов по SSH/SCP."""

    MAX_FILE_SIZE = None

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._sftp: paramiko.SFTPClient | None = None
        self._transport: paramiko.Transport | None = None

    @property
    def name(self) -> str:
        return "SSH"

    @property
    def type(self) -> str:
        return "ssh"

    def _get_sftp(self) -> paramiko.SFTPClient:
        """Получить SFTP соединение."""
        if self._sftp is None:
            host = self.config.get("host", "")
            port = self.config.get("port", 22)
            username = self.config.get("username", "")
            password = self.config.get("password", "")
            private_key_path = self.config.get("private_key_path", "")

            # Создаем транспорт
            self._transport = paramiko.Transport((host, port))

            # Авторизация
            if private_key_path and os.path.exists(private_key_path):
                key = paramiko.RSAKey.from_private_key_file(private_key_path)
                self._transport.connect(username=username, pkey=key)
            else:
                self._transport.connect(username=username, password=password)

            self._sftp = paramiko.SFTPClient.from_transport(self._transport)

        return self._sftp

    def test_connection(self) -> tuple[bool, str]:
        """Проверить подключение по SSH."""
        try:
            sftp = self._get_sftp()
            sftp.stat(".")  # Проверяем доступность
            return True, f"SSH подключен: {self.config.get('host')}"
        except Exception as e:
            self._close()
            return False, f"Ошибка SSH: {e}"

    def upload_file(self, file_path: str, remote_path: str | None = None) -> tuple[bool, str]:
        """Загрузить файл по SFTP."""
        try:
            sftp = self._get_sftp()
            remote_dir = self.config.get("remote_path", "/")

            # Создаем директорию если не существует
            try:
                sftp.stat(remote_dir)
            except Exception:
                sftp.mkdir(remote_dir)

            filename = os.path.basename(file_path)
            if remote_path:
                filename = remote_path

            remote_full_path = f"{remote_dir}/{filename}"

            sftp.put(file_path, remote_full_path)
            return True, remote_full_path
        except Exception as e:
            return False, str(e)

    def upload_data(self, data: bytes, remote_name: str) -> tuple[bool, str]:
        """Загрузить данные по SFTP."""
        try:
            sftp = self._get_sftp()
            remote_dir = self.config.get("remote_path", "/")

            try:
                sftp.stat(remote_dir)
            except Exception:
                sftp.mkdir(remote_dir)

            remote_full_path = f"{remote_dir}/{remote_name}"

            # Пишем из памяти через временный файл
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name

            try:
                sftp.put(tmp_path, remote_full_path)
                return True, remote_full_path
            finally:
                os.unlink(tmp_path)

        except Exception as e:
            return False, str(e)

    def _close(self):
        """Закрыть соединение."""
        if self._sftp:
            try:
                self._sftp.close()
            except Exception:
                pass
            self._sftp = None
        if self._transport:
            try:
                self._transport.close()
            except Exception:
                pass
            self._transport = None

    def close(self):
        """Закрыть соединение."""
        self._close()
