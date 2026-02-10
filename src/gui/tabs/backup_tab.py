"""Вкладка бэкапа."""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import customtkinter as ctk

from ...core.database import Database
from ...models import BackupPoint, ConnectionConfig
from ...core.archive_utils import ArchiveUtils


class BackupTab(ctk.CTkFrame):
    """Вкладка для создания и запуска бэкапов."""

    def __init__(self, parent, db: Database):
        """Инициализация."""
        super().__init__(parent)
        self.db = db
        self.backup_points = []
        self.connections = []

        self._create_ui()

    def _create_ui(self):
        """Создать интерфейс."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Верхняя панель
        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(frame, text="Точка бэкапа:").pack(side="left", padx=10)

        self.combo_backup_point = ctk.CTkComboBox(frame, values=[""], command=self._on_backup_point_selected)
        self.combo_backup_point.pack(side="left", padx=10, fill="x", expand=True)

        ctk.CTkButton(frame, text="+", width=30, command=self._add_backup_point).pack(side="left", padx=5)
        ctk.CTkButton(frame, text="-", width=30, command=self._delete_backup_point).pack(side="left", padx=5)

        # Средняя панель
        frame = ctk.CTkFrame(self)
        frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(frame, text="Исходная папка:").pack(side="left", padx=10)

        self.entry_source = ctk.CTkEntry(frame, placeholder_text="Выберите папку для бэкапа")
        self.entry_source.pack(side="left", padx=10, fill="x", expand=True)

        ctk.CTkButton(frame, text="Обзор...", command=self._browse_source).pack(side="left", padx=10)

        # Целевые хранилища
        frame = ctk.CTkFrame(self)
        frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(frame, text="Целевые хранилища:").pack(side="top", padx=10, pady=5)

        self.checkbox_targets = []
        self.targets_frame = frame

        # Кнопка запуска
        frame = ctk.CTkFrame(self)
        frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        self.btn_start = ctk.CTkButton(frame, text="Запустить бэкап", command=self._start_backup)
        self.btn_start.pack(side="left", padx=10)

        self.progress = ctk.CTkProgressBar(frame)
        self.progress.set(0)
        self.progress.pack(side="left", padx=10, fill="x", expand=True)

        # Лог
        frame = ctk.CTkFrame(self)
        frame.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")

        self.log_text = scrolledtext.ScrolledText(frame, height=10, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.grid_rowconfigure(4, weight=1)

    def refresh_connections(self):
        """Обновить список подключений."""
        self.connections = self.db.get_all_connections()
        self._update_checkboxes()

    def _update_checkboxes(self):
        """Обновить чекбоксы целевых хранилищ."""
        for checkbox_data in self.checkbox_targets:
            checkbox_data[1].destroy()

        self.checkbox_targets = []

        for conn in self.connections:
            var = tk.BooleanVar()
            checkbox = ctk.CTkCheckBox(self.targets_frame, text=str(conn), variable=var)
            checkbox.pack(side="top", padx=20, anchor="w")
            self.checkbox_targets.append((conn, checkbox, var))

    def _add_backup_point(self):
        """Добавить новую точку бэкапа."""
        point = BackupPoint(name="Новая точка", source_path="", target_ids=[])
        self.db.add_backup_point(point)
        self.backup_points.append(point)
        self._refresh_backup_points_combo()

    def _delete_backup_point(self):
        """Удалить выбранную точку бэкапа."""
        selected = self.combo_backup_point.get()
        if not selected:
            return

        for point in self.backup_points:
            if str(point) == selected:
                if messagebox.askyesno("Подтверждение", f"Удалить точку '{point.name}'?"):
                    self.db.delete_backup_point(point.id)
                    self.backup_points.remove(point)
                    self._refresh_backup_points_combo()
                    self._clear_form()
                break

    def _on_backup_point_selected(self, selected):
        """При выборе точки бэкапа."""
        for point in self.backup_points:
            if str(point) == selected:
                self.entry_source.delete(0, "end")
                self.entry_source.insert(0, point.source_path)
                for conn, checkbox, var in self.checkbox_targets:
                    var.set(conn.id in point.target_ids)
                break

    def _browse_source(self):
        """Выбрать папку."""
        path = filedialog.askdirectory(title="Выберите папку для бэкапа")
        if path:
            self.entry_source.delete(0, "end")
            self.entry_source.insert(0, path)

    def _start_backup(self):
        """Запустить бэкап."""
        source = self.entry_source.get()
        if not source:
            messagebox.showerror("Ошибка", "Выберите исходную папку")
            return

        targets = []
        for conn, checkbox, var in self.checkbox_targets:
            if var.get():
                targets.append(conn)

        if not targets:
            messagebox.showerror("Ошибка", "Выберите хотя бы одно целевое хранилище")
            return

        self.btn_start.configure(state="disabled")
        self.progress.set(0)

        thread = threading.Thread(target=self._backup_worker, args=(source, targets), daemon=True)
        thread.start()

    def _backup_worker(self, source: str, targets: list[ConnectionConfig]):
        """Воркер для выполнения бэкапа."""
        try:
            self._log(f"Начинаем бэкап: {source}")

            archive_path = os.path.join(os.path.dirname(source), f"backup_{os.path.basename(source)}.zip")
            self._log("Создаем архив...")

            ArchiveUtils.create_zip_archive(source, archive_path, progress_callback=self._archive_progress)

            self._log(f"Архив создан: {archive_path}")

            file_hash = ArchiveUtils.calculate_file_hash(archive_path)
            self._log(f"Хеш файла: {file_hash}")

            for conn in targets:
                self._log(f"Загружаем в {conn.name}...")

                if self.db.is_file_uploaded(file_hash, conn.id):
                    self._log(f"Файл уже загружен в {conn.name}, пропускаем")
                    continue

                success, result = conn.upload_file(archive_path)
                if success:
                    self._log(f"Загружено: {result}")
                    self._save_to_history(archive_path, file_hash, conn.id)
                else:
                    self._log(f"Ошибка загрузки в {conn.name}: {result}")

            self._log("Бэкап завершен!")
            self.progress.set(1)

        except Exception as e:
            self._log(f"Ошибка: {e}")
        finally:
            self.btn_start.configure(state="normal")

    def _archive_progress(self, filename: str, current: int, total: int):
        """Прогресс создания архива."""
        percent = current / total if total > 0 else 0
        self.progress.set(percent * 0.5)

    def _save_to_history(self, file_path: str, file_hash: str, target_id: str):
        """Сохранить информацию о загруженном файле."""
        from ...models import FileRecord
        record = FileRecord(
            backup_point_id="", file_path=file_path, file_hash=file_hash,
            file_size=os.path.getsize(file_path), targets=[target_id],
        )
        self.db.add_file_record(record)

    def _log(self, message: str):
        """Вывести сообщение в лог."""
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{self._get_timestamp()}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _get_timestamp(self):
        """Получить текущее время."""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def _refresh_backup_points_combo(self):
        """Обновить комбобокс точек бэкапа."""
        self.backup_points = self.db.get_all_backup_points()
        values = [str(p) for p in self.backup_points]
        values.insert(0, "")
        self.combo_backup_point.configure(values=values)

    def _clear_form(self):
        """Очистить форму."""
        self.entry_source.delete(0, "end")
        for conn, checkbox, var in self.checkbox_targets:
            var.set(False)
