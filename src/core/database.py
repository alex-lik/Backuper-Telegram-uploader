"""Модуль работы с SQLite базой данных."""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from ..models import BackupPoint, ConnectionConfig, FileRecord


class Database:
    """Работа с SQLite базой данных."""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            base_dir = Path(__file__).parent.parent.parent
            db_path = str(base_dir / "data" / "backup_history.db")
        self.db_path = db_path
        self._ensure_db_exists()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_db_exists(self):
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backup_points (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    schedule TEXT,
                    compression_level INTEGER DEFAULT 6,
                    exclude_patterns TEXT,
                    created_at TEXT NOT NULL,
                    last_run TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS connection_configs (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    config TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_records (
                    id TEXT PRIMARY KEY,
                    backup_point_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    targets TEXT,
                    archive_parts TEXT,
                    FOREIGN KEY (backup_point_id) REFERENCES backup_points(id)
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_hash ON file_records(file_hash)")
            conn.commit()
        finally:
            conn.close()

    def add_backup_point(self, point: BackupPoint) -> str:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO backup_points VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (point.id, point.name, point.source_path, point.schedule,
                 point.compression_level, json.dumps(point.exclude_patterns),
                 point.created_at.isoformat(), point.last_run.isoformat() if point.last_run else None),
            )
            conn.commit()
            return point.id
        finally:
            conn.close()

    def get_backup_point(self, point_id: str) -> BackupPoint | None:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM backup_points WHERE id = ?", (point_id,))
            row = cursor.fetchone()
            if row:
                return BackupPoint(
                    id=row["id"], name=row["name"], source_path=row["source_path"],
                    schedule=row["schedule"], compression_level=row["compression_level"],
                    exclude_patterns=json.loads(row["exclude_patterns"] or "[]"),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    last_run=datetime.fromisoformat(row["last_run"]) if row["last_run"] else None,
                )
            return None
        finally:
            conn.close()

    def get_all_backup_points(self) -> list[BackupPoint]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM backup_points ORDER BY created_at DESC")
            return [
                BackupPoint(
                    id=row["id"], name=row["name"], source_path=row["source_path"],
                    schedule=row["schedule"], compression_level=row["compression_level"],
                    exclude_patterns=json.loads(row["exclude_patterns"] or "[]"),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    last_run=datetime.fromisoformat(row["last_run"]) if row["last_run"] else None,
                ) for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def delete_backup_point(self, point_id: str) -> bool:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM backup_points WHERE id = ?", (point_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def update_backup_point(self, point: BackupPoint) -> bool:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE backup_points SET name=?, source_path=?, schedule=?, compression_level=?, exclude_patterns=?, last_run=? WHERE id=?""",
                (point.name, point.source_path, point.schedule, point.compression_level,
                 json.dumps(point.exclude_patterns), point.last_run.isoformat() if point.last_run else None, point.id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def add_connection(self, config: ConnectionConfig) -> str:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO connection_configs VALUES (?, ?, ?, ?, ?)""",
                (config.id, config.name, config.type.value, json.dumps(config.config), config.created_at.isoformat()),
            )
            conn.commit()
            return config.id
        finally:
            conn.close()

    def get_connection(self, config_id: str) -> ConnectionConfig | None:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM connection_configs WHERE id = ?", (config_id,))
            row = cursor.fetchone()
            if row:
                return ConnectionConfig(
                    id=row["id"], name=row["name"], type=row["type"],
                    config=json.loads(row["config"]), created_at=datetime.fromisoformat(row["created_at"]),
                )
            return None
        finally:
            conn.close()

    def get_all_connections(self) -> list[ConnectionConfig]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM connection_configs ORDER BY created_at DESC")
            return [
                ConnectionConfig(
                    id=row["id"], name=row["name"], type=row["type"],
                    config=json.loads(row["config"]), created_at=datetime.fromisoformat(row["created_at"]),
                ) for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def delete_connection(self, config_id: str) -> bool:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM connection_configs WHERE id = ?", (config_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def add_file_record(self, record: FileRecord) -> str:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO file_records VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (record.id, record.backup_point_id, record.file_path, record.file_hash,
                 record.file_size, record.uploaded_at.isoformat(),
                 json.dumps(record.targets), json.dumps(record.archive_parts)),
            )
            conn.commit()
            return record.id
        finally:
            conn.close()

    def get_files_by_backup_point(self, backup_point_id: str) -> list[FileRecord]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM file_records WHERE backup_point_id = ? ORDER BY uploaded_at DESC", (backup_point_id,))
            return [
                FileRecord(
                    id=row["id"], backup_point_id=row["backup_point_id"], file_path=row["file_path"],
                    file_hash=row["file_hash"], file_size=row["file_size"],
                    uploaded_at=datetime.fromisoformat(row["uploaded_at"]),
                    targets=json.loads(row["targets"] or "[]"), archive_parts=json.loads(row["archive_parts"] or "[]"),
                ) for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def is_file_uploaded(self, file_hash: str, target_id: str) -> bool:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM file_records WHERE file_hash = ? AND targets LIKE ?", (file_hash, f'%"{target_id}"%'))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def close(self):
        pass
