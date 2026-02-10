"""Модель записи о файле в истории бэкапов."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class FileRecord:
    """
    Запись о загруженном файле в истории.
    """

    backup_point_id: str
    file_path: str
    file_hash: str
    file_size: int
    targets: list[str] = field(default_factory=list)
    archive_parts: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    uploaded_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Сериализация в словарь."""
        return {
            "id": self.id,
            "backup_point_id": self.backup_point_id,
            "file_path": self.file_path,
            "file_hash": self.file_hash,
            "file_size": self.file_size,
            "uploaded_at": self.uploaded_at.isoformat(),
            "targets": self.targets,
            "archive_parts": self.archive_parts,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileRecord":
        """Десериализация из словаря."""
        return cls(
            id=data["id"],
            backup_point_id=data["backup_point_id"],
            file_path=data["file_path"],
            file_hash=data["file_hash"],
            file_size=data["file_size"],
            uploaded_at=datetime.fromisoformat(data["uploaded_at"]),
            targets=data.get("targets", []),
            archive_parts=data.get("archive_parts", []),
        )

    def is_uploaded_to(self, target_id: str) -> bool:
        """Проверка, загружен ли файл в указанное хранилище."""
        return target_id in self.targets

    def add_target(self, target_id: str):
        """Добавить хранилище, куда загружен файл."""
        if target_id not in self.targets:
            self.targets.append(target_id)

    def __str__(self) -> str:
        return f"{self.file_path} ({self.file_hash[:8]}...)"

    def __repr__(self) -> str:
        return f"FileRecord(id={self.id}, path={self.file_path}, hash={self.file_hash[:8]}...)"
