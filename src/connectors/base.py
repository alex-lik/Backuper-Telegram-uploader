"""Базовый класс для всех коннекторов хранилищ."""

from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """Базовый класс для коннекторов."""

    MAX_FILE_SIZE = None

    def __init__(self, config: dict[str, Any]):
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def type(self) -> str:
        pass

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        pass

    @abstractmethod
    def upload_file(self, file_path: str, remote_path: str | None = None) -> tuple[bool, str]:
        pass

    @abstractmethod
    def upload_data(self, data: bytes, remote_name: str) -> tuple[bool, str]:
        pass

    def get_max_file_size(self) -> int | None:
        return self.MAX_FILE_SIZE

    def __str__(self) -> str:
        return f"{self.name} ({self.type})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(config={self.config})"
