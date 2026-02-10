"""Модель настроек подключения к хранилищу."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .connection_type import ConnectionType


@dataclass
class ConnectionConfig:
    """
    Настройки подключения к хранилищу.
    """

    name: str
    type: ConnectionType
    config: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    # Telegram
    @property
    def bot_token(self) -> str:
        return self.config.get("bot_token", "")

    @bot_token.setter
    def bot_token(self, value: str):
        self.config["bot_token"] = value

    @property
    def chat_id(self) -> str:
        return self.config.get("chat_id", "")

    @chat_id.setter
    def chat_id(self, value: str):
        self.config["chat_id"] = value

    @property
    def is_premium(self) -> bool:
        return self.config.get("is_premium", False)

    @is_premium.setter
    def is_premium(self, value: bool):
        self.config["is_premium"] = value

    # S3/R2
    @property
    def endpoint(self) -> str:
        return self.config.get("endpoint", "")

    @endpoint.setter
    def endpoint(self, value: str):
        self.config["endpoint"] = value

    @property
    def bucket(self) -> str:
        return self.config.get("bucket", "")

    @bucket.setter
    def bucket(self, value: str):
        self.config["bucket"] = value

    @property
    def access_key(self) -> str:
        return self.config.get("access_key", "")

    @access_key.setter
    def access_key(self, value: str):
        self.config["access_key"] = value

    @property
    def secret_key(self) -> str:
        return self.config.get("secret_key", "")

    @secret_key.setter
    def secret_key(self, value: str):
        self.config["secret_key"] = value

    @property
    def region(self) -> str:
        return self.config.get("region", "us-east-1")

    @region.setter
    def region(self, value: str):
        self.config["region"] = value

    # FTP
    @property
    def host(self) -> str:
        return self.config.get("host", "")

    @host.setter
    def host(self, value: str):
        self.config["host"] = value

    @property
    def port(self) -> int:
        return self.config.get("port", 21)

    @port.setter
    def port(self, value: int):
        self.config["port"] = value

    @property
    def username(self) -> str:
        return self.config.get("username", "")

    @username.setter
    def username(self, value: str):
        self.config["username"] = value

    @property
    def password(self) -> str:
        return self.config.get("password", "")

    @password.setter
    def password(self, value: str):
        self.config["password"] = value

    @property
    def use_tls(self) -> bool:
        return self.config.get("use_tls", False)

    @use_tls.setter
    def use_tls(self, value: bool):
        self.config["use_tls"] = value

    # SSH
    @property
    def private_key_path(self) -> str:
        return self.config.get("private_key_path", "")

    @private_key_path.setter
    def private_key_path(self, value: str):
        self.config["private_key_path"] = value

    @property
    def remote_path(self) -> str:
        return self.config.get("remote_path", "/")

    @remote_path.setter
    def remote_path(self, value: str):
        self.config["remote_path"] = value

    # Google Drive
    @property
    def credentials_path(self) -> str:
        return self.config.get("credentials_path", "")

    @credentials_path.setter
    def credentials_path(self, value: str):
        self.config["credentials_path"] = value

    @property
    def folder_id(self) -> str:
        return self.config.get("folder_id", "")

    @folder_id.setter
    def folder_id(self, value: str):
        self.config["folder_id"] = value

    # Email
    @property
    def smtp_server(self) -> str:
        return self.config.get("smtp_server", "")

    @smtp_server.setter
    def smtp_server(self, value: str):
        self.config["smtp_server"] = value

    @property
    def smtp_port(self) -> int:
        return self.config.get("smtp_port", 587)

    @smtp_port.setter
    def smtp_port(self, value: int):
        self.config["smtp_port"] = value

    @property
    def to_email(self) -> str:
        return self.config.get("to_email", "")

    @to_email.setter
    def to_email(self, value: str):
        self.config["to_email"] = value

    # Local
    @property
    def local_path(self) -> str:
        return self.config.get("local_path", "")

    @local_path.setter
    def local_path(self, value: str):
        self.config["local_path"] = value

    def to_dict(self) -> dict[str, Any]:
        """Сериализация в словарь."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConnectionConfig":
        """Десериализация из словаря."""
        return cls(
            id=data["id"],
            name=data["name"],
            type=ConnectionType(data["type"]),
            config=data.get("config", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
        )

    def get_file_limit(self) -> int | None:
        """Получить лимит размера файла."""
        return ConnectionType.get_file_limit(self.type, self.is_premium if self.type == ConnectionType.TELEGRAM else False)

    def __str__(self) -> str:
        return f"{self.name} ({ConnectionType.display_name(self.type.value)})"

    def __repr__(self) -> str:
        return f"ConnectionConfig(id={self.id}, name={self.name}, type={self.type})"
