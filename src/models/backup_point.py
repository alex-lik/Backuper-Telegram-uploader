"""Модель точки бэкапа."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class BackupPoint:
    """
    Точка бэкапа - описание что и куда бэкапить.
    """

    name: str
    source_path: str
    target_ids: list[str] = field(default_factory=list)
    schedule: str | None = None
    exclude_patterns: list[str] = field(default_factory=list)
    compression_level: int = 6
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    last_run: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Сериализация в словарь."""
        return {
            "id": self.id,
            "name": self.name,
            "source_path": self.source_path,
            "target_ids": self.target_ids,
            "schedule": self.schedule,
            "exclude_patterns": self.exclude_patterns,
            "compression_level": self.compression_level,
            "created_at": self.created_at.isoformat(),
            "last_run": self.last_run.isoformat() if self.last_run else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackupPoint":
        """Десериализация из словаря."""
        return cls(
            id=data["id"],
            name=data["name"],
            source_path=data["source_path"],
            target_ids=data.get("target_ids", []),
            schedule=data.get("schedule"),
            exclude_patterns=data.get("exclude_patterns", []),
            compression_level=data.get("compression_level", 6),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_run=datetime.fromisoformat(data["last_run"]) if data.get("last_run") else None,
        )

    def __str__(self) -> str:
        return f"{self.name} ({self.source_path})"

    def __repr__(self) -> str:
        return f"BackupPoint(id={self.id}, name={self.name}, source={self.source_path})"
