"""Утилиты для архивации и разбиения файлов."""

import hashlib
import os
import shutil
import zipfile
from pathlib import Path
from typing import Callable


class ArchiveUtils:
    """
    Утилиты для создания архивов и разбиения на части.
    """

    CHUNK_SIZE = 1024 * 1024  # 1 MB для чтения файлов

    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """
        Вычислить MD5 хеш файла.

        Args:
            file_path: Путь к файлу

        Returns:
            MD5 хеш в виде строки
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            while chunk := f.read(ArchiveUtils.CHUNK_SIZE):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def calculate_data_hash(data: bytes) -> str:
        """
        Вычислить MD5 хеш данных в памяти.

        Args:
            data: Байты данных

        Returns:
            MD5 хеш в виде строки
        """
        return hashlib.md5(data).hexdigest()

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        Получить размер файла в байтах.

        Args:
            file_path: Путь к файлу

        Returns:
            Размер файла в байтах
        """
        return os.path.getsize(file_path)

    @staticmethod
    def should_split_file(file_size: int, max_size: int | None) -> bool:
        """
        Проверить, нужно ли разбивать файл.

        Args:
            file_size: Размер файла в байтах
            max_size: Максимальный размер файла

        Returns:
            True если нужно разбивать
        """
        if max_size is None:
            return False
        return file_size > max_size

    @staticmethod
    def split_file(
        file_path: str,
        output_dir: str,
        max_chunk_size: int,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[str]:
        """
        Разбить файл на части.

        Args:
            file_path: Путь к исходному файлу
            output_dir: Директория для сохранения частей
            max_chunk_size: Максимальный размер части в байтах
            progress_callback: Колбэк для отображения прогресса (current, total)

        Returns:
            Список путей к созданным частям
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        file_size = os.path.getsize(file_path)
        file_name = Path(file_path).stem
        file_ext = Path(file_path).suffix

        parts = []
        part_num = 1

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(max_chunk_size)
                if not chunk:
                    break

                part_path = os.path.join(output_dir, f"{file_name}.part{part_num:03d}{file_ext}")
                with open(part_path, "wb") as part_file:
                    part_file.write(chunk)

                parts.append(part_path)
                part_num += 1

                if progress_callback:
                    progress_callback(f.tell(), file_size)

        return parts

    @staticmethod
    def merge_files(
        parts: list[str],
        output_path: str,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> None:
        """
        Собрать файл из частей.

        Args:
            parts: Список путей к частям (в порядке)
            output_path: Путь к результату
            progress_callback: Колбэк для отображения прогресса
        """
        total_size = sum(os.path.getsize(p) for p in parts)
        current_size = 0

        with open(output_path, "wb") as out:
            for part_path in parts:
                with open(part_path, "rb") as part:
                    while chunk := part.read(ArchiveUtils.CHUNK_SIZE):
                        out.write(chunk)
                        current_size += len(chunk)
                        if progress_callback:
                            progress_callback(current_size, total_size)

    @staticmethod
    def create_zip_archive(
        source_path: str,
        output_path: str,
        compression_level: int = 6,
        exclude_patterns: list[str] | None = None,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> str:
        """
        Создать ZIP архив из папки или файла.

        Args:
            source_path: Путь к исходному файлу или папке
            output_path: Путь к создаваемому архиву
            compression_level: Уровень сжатия (0-9)
            exclude_patterns: Паттерны для исключения
            progress_callback: Колбэк (filename, current, total)

        Returns:
            Путь к созданному архиву
        """
        exclude_patterns = exclude_patterns or []

        source = Path(source_path)
        compression = zipfile.ZIP_DEFLATED if compression_level > 0 else zipfile.ZIP_STORED

        total_files = sum(1 for _ in source.rglob("*") if _.is_file())
        processed = 0

        with zipfile.ZipFile(output_path, "w", compression, compresslevel=compression_level) as zf:
            for file_path in source.rglob("*"):
                if file_path.is_file():
                    # Проверка паттернов исключения
                    rel_path = str(file_path.relative_to(source))
                    should_exclude = False
                    for pattern in exclude_patterns:
                        if pattern in rel_path:
                            should_exclude = True
                            break

                    if should_exclude:
                        continue

                    # Добавляем файл в архив
                    arcname = file_path.relative_to(source.parent)
                    zf.write(file_path, arcname)

                    processed += 1
                    if progress_callback:
                        progress_callback(str(file_path), processed, total_files)

        return output_path

    @staticmethod
    def create_split_zip_archive(
        source_path: str,
        output_dir: str,
        max_part_size: int,
        compression_level: int = 6,
        exclude_patterns: list[str] | None = None,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> list[str]:
        """
        Создать ZIP архив с разбиением на части.

        Args:
            source_path: Путь к исходному файлу или папке
            output_dir: Директория для сохранения
            max_part_size: Максимальный размер части
            compression_level: Уровень сжатия
            exclude_patterns: Паттерны для исключения
            progress_callback: Колбэк

        Returns:
            Список путей к частям архива
        """
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        source = Path(source_path)
        archive_name = source.name + ".zip"
        temp_archive = os.path.join(output_dir, archive_name)

        # Создаем полный архив во временную папку
        temp_dir = os.path.join(output_dir, "_temp_archive")
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        temp_archive_path = os.path.join(temp_dir, archive_name)

        ArchiveUtils.create_zip_archive(
            source_path,
            temp_archive_path,
            compression_level,
            exclude_patterns,
            progress_callback,
        )

        # Разбиваем архив на части
        parts = ArchiveUtils.split_file(temp_archive_path, output_dir, max_part_size)

        # Удаляем временный архив
        shutil.rmtree(temp_dir)

        return parts

    @staticmethod
    def get_directory_size(path: str) -> int:
        """
        Получить общий размер директории в байтах.

        Args:
            path: Путь к директории

        Returns:
            Общий размер в байтах
        """
        total = 0
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += ArchiveUtils.get_directory_size(entry.path)
        return total

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        Форматировать размер в человекочитаемый вид.

        Args:
            size_bytes: Размер в байтах

        Returns:
            Отформатированная строка (KB, MB, GB)
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"
