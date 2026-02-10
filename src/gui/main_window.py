"""Главное окно приложения."""

import customtkinter as ctk

from ..core.database import Database
from .tabs.backup_tab import BackupTab
from .tabs.connections_tab import ConnectionsTab
from .tabs.history_tab import HistoryTab


class MainWindow(ctk.CTk):
    """Главное окно приложения."""

    def __init__(self):
        """Инициализация главного окна."""
        super().__init__()

        self.title("Backuper - Telegram Uploader")
        self.geometry("1000x700")

        self.db = Database()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_ui()
        self._refresh_data()

    def _create_ui(self):
        """Создать интерфейс."""
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.tab_backup = self.tabview.add("Бэкап")
        self.tab_connections = self.tabview.add("Подключения")
        self.tab_history = self.tabview.add("История")

        self.backup_tab = BackupTab(self.tab_backup, self.db)
        self.backup_tab.pack(fill="both", expand=True, padx=10, pady=10)

        self.connections_tab = ConnectionsTab(self.tab_connections, self.db)
        self.connections_tab.pack(fill="both", expand=True, padx=10, pady=10)

        self.history_tab = HistoryTab(self.tab_history, self.db)
        self.history_tab.pack(fill="both", expand=True, padx=10, pady=10)

        self.tabview.set("Бэкап")

    def _refresh_data(self):
        """Обновить данные."""
        if hasattr(self, 'backup_tab'):
            self.backup_tab.refresh_connections()
        if hasattr(self, 'connections_tab'):
            self.connections_tab.refresh_connections()
        if hasattr(self, 'history_tab'):
            self.history_tab.refresh_history()

    def run(self):
        """Запустить приложение."""
        self.mainloop()

    def destroy(self):
        """Закрыть приложение."""
        self.db.close()
        super().destroy()
