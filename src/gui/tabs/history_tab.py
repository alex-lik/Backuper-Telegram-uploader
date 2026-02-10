"""Вкладка истории бэкапов."""

import customtkinter as ctk
from tkinter import messagebox

from ...core.database import Database
from ...core.archive_utils import ArchiveUtils


class HistoryTab(ctk.CTkFrame):
    """Вкладка для просмотра истории бэкапов."""

    def __init__(self, parent, db: Database):
        """Инициализация."""
        super().__init__(parent)
        self.db = db
        self.records = []

        self._create_ui()

    def _create_ui(self):
        """Создать интерфейс."""
        # Настройка сетки
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Фильтры
        self._create_filters()

        # Таблица
        self._create_table()

    def _create_filters(self):
        """Секция фильтров."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(frame, text="Поиск:").pack(side="left", padx=10)

        self.entry_search = ctk.CTkEntry(frame, placeholder_text="Поиск по имени файла...")
        self.entry_search.pack(side="left", padx=10, fill="x", expand=True)
        self.entry_search.bind("<KeyRelease>", self._on_search)

        ctk.CTkButton(frame, text="Обновить", command=self.refresh_history).pack(side="left", padx=10)

    def _create_table(self):
        """Создать таблицу истории."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Заголовки
        headers = ["Файл", "Размер", "Хеш", "Дата", "Загружен в"]
        weights = [3, 1, 2, 1.5, 2]

        for i, (header, weight) in enumerate(zip(headers, weights)):
            ctk.CTkLabel(frame, text=header, font=("Arial", 12, "bold")).grid(row=0, column=i, padx=2, pady=5, sticky="w")

        # Список
        self.list_frame = ctk.CTkScrollableFrame(frame)
        self.list_frame.grid(row=1, column=0, columnspan=len(headers), padx=2, pady=5, sticky="nsew")

        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self.labels = []

    def refresh_history(self):
        """Обновить историю."""
        self.records = []
        for point in self.db.get_all_backup_points():
            point_records = self.db.get_files_by_backup_point(point.id)
            self.records.extend(point_records)

        self._update_list()

    def _update_list(self, filter_text: str = ""):
        """Обновить отображение списка."""
        # Очищаем старые
        for label in self.labels:
            label.destroy()

        self.labels = []

        # Фильтруем
        filtered = self.records
        if filter_text:
            filter_lower = filter_text.lower()
            filtered = [r for r in filtered if filter_lower in r.file_path.lower()]

        # Добавляем
        for i, record in enumerate(filtered[:50]):  # Ограничиваем 50 записями
            # Имя файла
            name_label = ctk.CTkLabel(self.list_frame, text=record.file_path)
            name_label.grid(row=i, column=0, padx=2, pady=2, sticky="w")
            self.labels.append(name_label)

            # Размер
            size_label = ctk.CTkLabel(self.list_frame, text=ArchiveUtils.format_size(record.file_size))
            size_label.grid(row=i, column=1, padx=2, pady=2, sticky="w")
            self.labels.append(size_label)

            # Хеш
            hash_label = ctk.CTkLabel(self.list_frame, text=record.file_hash[:12] + "...")
            hash_label.grid(row=i, column=2, padx=2, pady=2, sticky="w")
            self.labels.append(hash_label)

            # Дата
            from datetime import datetime
            date_label = ctk.CTkLabel(self.list_frame, text=record.uploaded_at.strftime("%Y-%m-%d %H:%M"))
            date_label.grid(row=i, column=3, padx=2, pady=2, sticky="w")
            self.labels.append(date_label)

            # Куда загружен
            targets = ", ".join(record.targets[:3])
            if len(record.targets) > 3:
                targets += f" +{len(record.targets) - 3}"
            targets_label = ctk.CTkLabel(self.list_frame, text=targets)
            targets_label.grid(row=i, column=4, padx=2, pady=2, sticky="w")
            self.labels.append(targets_label)

    def _on_search(self, event):
        """При изменении поиска."""
        self._update_list(self.entry_search.get())
