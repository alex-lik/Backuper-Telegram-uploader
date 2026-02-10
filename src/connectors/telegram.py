"""Коннектор для Telegram."""

import os
import time
from pathlib import Path
from typing import Any

from telegram import Bot
from telegram.error import TelegramError

from .base import BaseConnector


class TelegramConnector(BaseConnector):
    """Коннектор для загрузки файлов в Telegram."""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._bot: Bot | None = None

    @property
    def name(self) -> str:
        return "Telegram"

    @property
    def type(self) -> str:
        return "telegram"

    @property
    def MAX_FILE_SIZE(self) -> int | None:
        """Лимит зависит от премиума."""
        return 4 * 1024**3 if self.config.get("is_premium", False) else 2 * 1024**3

    def _get_bot(self) -> Bot:
        """Получить экземпляр бота."""
        if self._bot is None:
            token = self.config.get("bot_token", "")
            if not token:
                raise ValueError("Bot token не указан")
            self._bot = Bot(token=token)
        return self._bot

    def test_connection(self) -> tuple[bool, str]:
        """Проверить подключение к Telegram."""
        try:
            bot = self._get_bot()
            me = bot.get_me()
            chat_id = self.config.get("chat_id", "")
            if chat_id:
                bot.get_chat(chat_id)
            return True, f"Бот @{me.username} подключен"
        except TelegramError as e:
            return False, f"Ошибка Telegram: {e}"
        except Exception as e:
            return False, str(e)

    def upload_file(self, file_path: str, remote_path: str | None = None) -> tuple[bool, str]:
        """Загрузить файл в Telegram."""
        try:
            bot = self._get_bot()
            chat_id = self.config.get("chat_id", "")
            if not chat_id:
                return False, "Chat ID не указан"

            filename = os.path.basename(file_path)
            if remote_path:
                filename = remote_path

            # Отправляем документ
            with open(file_path, "rb") as f:
                message = bot.send_document(
                    chat_id=chat_id,
                    document=f,
                    filename=filename,
                    timeout=300,
                )

            return True, f"message_{message.message_id}"
        except TelegramError as e:
            return False, f"Ошибка Telegram: {e}"
        except Exception as e:
            return False, str(e)

    def upload_data(self, data: bytes, remote_name: str) -> tuple[bool, str]:
        """Загрузить данные в Telegram."""
        try:
            bot = self._get_bot()
            chat_id = self.config.get("chat_id", "")
            if not chat_id:
                return False, "Chat ID не указан"

            # Сохраняем во временный файл
            temp_dir = Path.home() / ".backuper_temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_file = temp_dir / remote_name

            with open(temp_file, "wb") as f:
                f.write(data)

            try:
                with open(temp_file, "rb") as f:
                    message = bot.send_document(
                        chat_id=chat_id,
                        document=f,
                        filename=remote_name,
                        timeout=300,
                    )
                return True, f"message_{message.message_id}"
            finally:
                temp_file.unlink(missing_ok=True)

        except TelegramError as e:
            return False, f"Ошибка Telegram: {e}"
        except Exception as e:
            return False, str(e)

    def download_file(self, message_id: str) -> bytes | None:
        """Скачать файл из Telegram (для восстановления)."""
        try:
            bot = self._get_bot()
            chat_id = self.config.get("chat_id", "")
            if not chat_id:
                return None

            message_id = message_id.replace("message_", "")
            message = bot.get_message(chat_id, int(message_id))

            if message.document:
                file = bot.get_file(message.document.file_id)
                return file.download_as_bytes()

            return None
        except Exception:
            return None

    def delete_file(self, message_id: str) -> tuple[bool, str]:
        """Удалить файл из Telegram."""
        # Telegram не позволяет удалять сообщения бота
        return False, "Удаление сообщений не поддерживается"
