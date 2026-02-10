"""Коннектор для FTP."""

import os
from ftplib import FTP, FTP_TLS
from pathlib import Path
from typing import Any

from .base import BaseConnector


class FTPConnector(BaseConnector):
    """Коннектор для загрузки файлов по FTP."""

    MAX_FILE_SIZE = None

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._ftp: FTP | FTP_TLS | None = None

    @property
    def name(self) -> str:
        return "FTP"

    @property
    def type(self) -> str:
        return "ftp"

    def _get_ftp_connection(self) -> FTP | FTP_TLS:
        """Получить соединение с FTP."""
        if self._ftp is None:
            host = self.config.get("host", "")
            port = self.config.get("port", 21)
            username = self.config.get("username", "anonymous")
            password = self.config.get("password", "")
            use_tls = self.config.get("use_tls", False)

            if use_tls:
                self._ftp = FTP_TLS()
                self._ftp.encoding = "utf-8"
                self._ftp.connect(host, port)
                self._ftp.login(username, password)
                self._ftp.prot_p()  # Включить защищенный режим
            else:
                self._ftp = FTP()
                self._ftp.encoding = "utf-8"
                self._ftp.connect(host, port)
                self._ftp.login(username, password)

        return self._ftp

    def test_connection(self) -> tuple[bool, str]:
        """Проверить подключение к FTP."""
        try:
            ftp = self._get_ftp_connection()
            ftp.voidcmd("NOOP")  # Проверяем соединение
            return True, f"FTP подключен: {self.config.get('host')}"
        except Exception as e:
            self._ftp = None
            return False, f"Ошибка FTP: {e}"

    def upload_file(self, file_path: str, remote_path: str | None = None) -> tuple[bool, str]:
        """Загрузить файл на FTP."""
        try:
            ftp = self._get_ftp_connection()
            remote_dir = self.config.get("remote_dir", "/")

            # Переходим в директорию
            try:
                ftp.cwd(remote_dir)
            except Exception:
                # Создаем директорию если не существует
                parts = remote_dir.strip("/").split("/")
                current = "/"
                for part in parts:
                    if part:
                        current += part + "/"
                        try:
                            ftp.cwd(current)
                        except Exception:
                            ftp.mkd(current)
                            ftp.cwd(current)

            filename = os.path.basename(file_path)
            if remote_path:
                filename = remote_path

            # Загружаем файл
            with open(file_path, "rb") as f:
                ftp.storbinary(f"STOR {filename}", f)

            return True, f"{remote_dir}/{filename}"
        except Exception as e:
            return False, str(e)

    def upload_data(self, data: bytes, remote_name: str) -> tuple[bool, str]:
        """Загрузить данные на FTP."""
        try:
            ftp = self._get_ftp_connection()
            remote_dir = self.config.get("remote_dir", "/")

            try:
                ftp.cwd(remote_dir)
            except Exception:
                parts = remote_dir.strip("/").split("/")
                current = "/"
                for part in parts:
                    if part:
                        current += part + "/"
                        try:
                            ftp.cwd(current)
                        except Exception:
                            ftp.mkd(current)
                            ftp.cwd(current)

            # Загружаем из памяти через временный файл
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(data)
                tmp_path = tmp.name

            try:
                with open(tmp_path, "rb") as f:
                    ftp.storbinary(f"STOR {remote_name}", f)
                return True, f"{remote_dir}/{remote_name}"
            finally:
                os.unlink(tmp_path)

        except Exception as e:
            return False, str(e)

    def close(self):
        """Закрыть соединение."""
        if self._ftp:
            try:
                self._ftp.quit()
            except Exception:
                self._ftp.close()
            self._ftp = None
