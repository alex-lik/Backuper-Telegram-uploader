"""Коннектор для отправки бэкапов по email."""

import os
import smtplib
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from .base import BaseConnector


class EmailConnector(BaseConnector):
    """Коннектор для отправки бэкапов по email."""

    MAX_FILE_SIZE = 25 * 1024**2  # 25 MB typical

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

    @property
    def name(self) -> str:
        return "Email"

    @property
    def type(self) -> str:
        return "email"

    def test_connection(self) -> tuple[bool, str]:
        """Проверить подключение к SMTP."""
        try:
            server = self.config.get("smtp_server", "")
            port = self.config.get("smtp_port", 587)

            # Просто проверяем что сервер доступен
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((server, port))
            sock.close()

            if result == 0:
                return True, f"SMTP сервер доступен: {server}:{port}"
            else:
                return False, f"SMTP сервер недоступен: {server}:{port}"
        except Exception as e:
            return False, str(e)

    def upload_file(self, file_path: str, remote_path: str | None = None) -> tuple[bool, str]:
        """Отправить файл по email."""
        return self._send_email_with_attachment(file_path)

    def upload_data(self, data: bytes, remote_name: str) -> tuple[bool, str]:
        """Отправить данные по email."""
        # Сохраняем во временный файл
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name

        try:
            result = self._send_email_with_attachment(tmp_path, remote_name)
            return result
        finally:
            os.unlink(tmp_path)

    def _send_email_with_attachment(self, file_path: str, filename: str | None = None) -> tuple[bool, str]:
        """Отправить email с вложением."""
        try:
            smtp_server = self.config.get("smtp_server", "")
            smtp_port = self.config.get("smtp_port", 587)
            username = self.config.get("username", "")
            password = self.config.get("password", "")
            from_email = self.config.get("from_email", username)
            to_email = self.config.get("to_email", "")

            if not to_email:
                return False, "Получатель не указан"

            # Создаем сообщение
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = f"Backup: {os.path.basename(file_path)}"

            # Тело письма
            body = f"Бэкап файла: {filename or os.path.basename(file_path)}\n"
            body += f"Дата: {Path(__file__).parent.stat(file_path).st_mtime}\n"
            msg.attach(MIMEText(body, "plain"))

            # Вложение
            attach_filename = filename or os.path.basename(file_path)
            with open(file_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
                encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {attach_filename}",
                )
                msg.attach(part)

            # Отправляем
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)

            return True, f"Отправлено на {to_email}"
        except smtplib.SMTPException as e:
            return False, f"Ошибка SMTP: {e}"
        except Exception as e:
            return False, str(e)

    def close(self):
        pass
