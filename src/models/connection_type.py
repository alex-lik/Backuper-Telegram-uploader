"""Типы подключений для бэкапа."""

from enum import Enum


class ConnectionType(str, Enum):
    """Типы хранилищ для бэкапа."""

    TELEGRAM = "telegram"
    S3 = "s3"
    R2 = "r2"
    FTP = "ftp"
    SSH = "ssh"
    GOOGLE_DRIVE = "google_drive"
    EMAIL = "email"
    LOCAL = "local"

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        """Возвращает список вариантов для UI."""
        return [(member.value, member.name.replace("_", " ").title()) for member in cls]

    @classmethod
    def display_name(cls, value: str) -> str:
        """Возвращает читаемое название типа."""
        for member in cls:
            if member.value == value:
                return member.name.replace("_", " ").title()
        return value

    @staticmethod
    def get_file_limit(connection_type: "ConnectionType", is_premium: bool = False) -> int | None:
        """
        Возвращает лимит размера файла для типа подключения.
        """
        limits = {
            ConnectionType.TELEGRAM: 2 * 1024**3 if not is_premium else 4 * 1024**3,
            ConnectionType.S3: None,
            ConnectionType.R2: None,
            ConnectionType.FTP: None,
            ConnectionType.SSH: None,
            ConnectionType.GOOGLE_DRIVE: 15 * 1024**3,
            ConnectionType.EMAIL: 25 * 1024**2,
            ConnectionType.LOCAL: None,
        }
        return limits.get(connection_type)
