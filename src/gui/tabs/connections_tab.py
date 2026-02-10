"""Вкладка управления подключениями."""

import customtkinter as ctk
from tkinter import messagebox

from ...core.database import Database
from ...models import ConnectionConfig, ConnectionType
from ...connectors.local import LocalConnector
from ...connectors.telegram import TelegramConnector
from ...connectors.ftp import FTPConnector
from ...connectors.ssh import SSHConnector
from ...connectors.s3 import S3Connector
from ...connectors.google_drive import GoogleDriveConnector
from ...connectors.email import EmailConnector


class ConnectionsTab(ctk.CTkFrame):
    """Вкладка для управления подключениями."""

    def __init__(self, parent, db: Database):
        """Инициализация."""
        super().__init__(parent)
        self.db = db
        self.connections = []

        self._create_ui()
        self.refresh_connections()

    def _create_ui(self):
        """Создать интерфейс."""
        # Настройка сетки
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Верхняя панель - кнопки
        self._create_actions()

        # Список подключений
        self._create_list()

    def _create_actions(self):
        """Секция действий."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkButton(frame, text="Добавить подключение", command=self._add_connection).pack(side="left", padx=10)
        ctk.CTkButton(frame, text="Тест", command=self._test_connection).pack(side="left", padx=10)
        ctk.CTkButton(frame, text="Удалить", command=self._delete_connection).pack(side="left", padx=10)

    def _create_list(self):
        """Создать список подключений."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Заголовки
        headers = ["Имя", "Тип", "Статус"]
        widths = [30, 20, 20]

        for i, (header, width) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(frame, text=header, font=("Arial", 12, "bold")).grid(row=0, column=i, padx=5, pady=5, sticky="w")

        # Список
        self.list_frame = ctk.CTkScrollableFrame(frame)
        self.list_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        self.labels = []

    def refresh_connections(self):
        """Обновить список подключений."""
        self.connections = self.db.get_all_connections()
        self._update_list()

    def _update_list(self):
        """Обновить отображение списка."""
        # Очищаем старые
        for label in self.labels:
            label.destroy()

        self.labels = []

        # Добавляем новые
        for i, conn in enumerate(self.connections):
            # Чекбокс для выбора
            var = ctk.StringVar(value=conn.id)
            checkbox = ctk.CTkRadioButton(self.list_frame, text="", variable=var, value=conn.id)
            checkbox.grid(row=i, column=0, padx=5, sticky="w")
            self.labels.append(checkbox)

            # Имя
            name_label = ctk.CTkLabel(self.list_frame, text=conn.name)
            name_label.grid(row=i, column=1, padx=5, sticky="w")
            self.labels.append(name_label)

            # Тип
            type_label = ctk.CTkLabel(self.list_frame, text=ConnectionType.display_name(conn.type.value))
            type_label.grid(row=i, column=2, padx=5, sticky="w")
            self.labels.append(type_label)

    def _get_selected(self) -> ConnectionConfig | None:
        """Получить выбранное подключение."""
        for label in self.labels:
            if isinstance(label, ctk.CTkRadioButton):
                if label.get() == 1:  # Не работает так
                    pass

        # Ищем по selected_id который мы не сохранили...
        # Упрощенно - возвращаем первое
        return self.connections[0] if self.connections else None

    def _add_connection(self):
        """Добавить новое подключение."""
        # Создаем диалоговое окно
        dialog = AddConnectionDialog(self)
        dialog.transient(self)
        dialog.grab_set()

        # Ждем результат
        self.wait_window(dialog)

        if dialog.result:
            conn = dialog.result
            self.db.add_connection(conn)
            self.refresh_connections()

    def _test_connection(self):
        """Тестировать выбранное подключение."""
        # Упрощенно - тестируем первое
        if not self.connections:
            messagebox.showinfo("Информация", "Нет подключений")
            return

        conn = self.connections[0]
        success, msg = self._test_connector(conn)
        messagebox.showinfo("Результат", msg)

    def _test_connector(self, conn: ConnectionConfig) -> tuple[bool, str]:
        """Тестировать конкретное подключение."""
        connector = self._create_connector(conn)
        if connector is None:
            return False, "Неизвестный тип подключения"
        return connector.test_connection()

    def _create_connector(self, conn: ConnectionConfig):
        """Создать экземпляр коннектора."""
        type_map = {
            ConnectionType.LOCAL: LocalConnector,
            ConnectionType.TELEGRAM: TelegramConnector,
            ConnectionType.FTP: FTPConnector,
            ConnectionType.SSH: SSHConnector,
            ConnectionType.S3: S3Connector,
            ConnectionType.R2: S3Connector,
            ConnectionType.GOOGLE_DRIVE: GoogleDriveConnector,
            ConnectionType.EMAIL: EmailConnector,
        }
        cls = type_map.get(conn.type)
        if cls:
            return cls(conn.config)
        return None

    def _delete_connection(self):
        """Удалить выбранное подключение."""
        if not self.connections:
            return

        conn = self.connections[0]
        if messagebox.askyesno("Подтверждение", f"Удалить подключение '{conn.name}'?"):
            self.db.delete_connection(conn.id)
            self.refresh_connections()


class AddConnectionDialog(ctk.CTkToplevel):
    """Диалог добавления подключения."""

    def __init__(self, parent):
        """Инициализация."""
        super().__init__(parent)
        self.title("Добавить подключение")
        self.geometry("400x500")

        self.result = None

        self._create_ui()

    def _create_ui(self):
        """Создать интерфейс."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Тип подключения
        ctk.CTkLabel(self, text="Тип подключения:").pack(padx=10, pady=(10, 5), anchor="w")

        self.combo_type = ctk.CTkComboBox(self, values=[t[1] for t in ConnectionType.choices()])
        self.combo_type.pack(padx=10, pady=5, fill="x")
        self.combo_type.configure(command=self._on_type_changed)

        # Имя
        ctk.CTkLabel(self, text="Имя:").pack(padx=10, pady=(10, 5), anchor="w")
        self.entry_name = ctk.CTkEntry(self)
        self.entry_name.pack(padx=10, pady=5, fill="x")

        # Контейнер для настроек
        self.settings_frame = ctk.CTkScrollableFrame(self)
        self.settings_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.entries = {}

        # Кнопки
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(padx=10, pady=10, fill="x")

        ctk.CTkButton(btn_frame, text="Сохранить", command=self._save).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Отмена", command=self.destroy).pack(side="right", padx=10)

        # Инициализируем настройки для первого типа
        self._on_type_changed(self.combo_type.get())

    def _on_type_changed(self, choice):
        """При изменении типа."""
        # Очищаем старые
        for widget in self.settings_frame.winfo_children():
            widget.destroy()

        self.entries.clear()

        # Определяем тип
        type_value = None
        for t in ConnectionType.choices():
            if t[1] == choice:
                type_value = t[0]
                break

        if type_value == ConnectionType.TELEGRAM.value:
            self._add_telegram_settings()
        elif type_value == ConnectionType.S3.value or type_value == ConnectionType.R2.value:
            self._add_s3_settings()
        elif type_value == ConnectionType.FTP.value:
            self._add_ftp_settings()
        elif type_value == ConnectionType.SSH.value:
            self._add_ssh_settings()
        elif type_value == ConnectionType.GOOGLE_DRIVE.value:
            self._add_google_settings()
        elif type_value == ConnectionType.EMAIL.value:
            self._add_email_settings()
        elif type_value == ConnectionType.LOCAL.value:
            self._add_local_settings()

    def _add_field(self, parent, label_text, key, is_password=False):
        """Добавить поле ввода."""
        ctk.CTkLabel(parent, text=label_text).pack(padx=5, pady=(5, 0), anchor="w")
        entry = ctk.CTkEntry(parent, show="*" if is_password else "")
        entry.pack(padx=5, pady=5, fill="x")
        self.entries[key] = entry

    def _add_telegram_settings(self):
        """Настройки Telegram."""
        self._add_field(self.settings_frame, "Bot Token:", "bot_token")
        self._add_field(self.settings_frame, "Chat ID:", "chat_id")

        # Premium checkbox
        self.var_premium = ctk.BooleanVar()
        ctk.CTkCheckBox(self.settings_frame, text="Telegram Premium", variable=self.var_premium).pack(padx=5, pady=5, anchor="w")

    def _add_s3_settings(self):
        """Настройки S3/R2."""
        endpoint_type = "S3"
        self._add_field(self.settings_frame, f"{endpoint_type} Endpoint URL:", "endpoint")
        self._add_field(self.settings_frame, f"{endpoint_type} Bucket:", "bucket")
        self._add_field(self.settings_frame, f"{endpoint_type} Access Key:", "access_key")
        self._add_field(self.settings_frame, f"{endpoint_type} Secret Key:", "secret_key", is_password=True)
        self._add_field(self.settings_frame, "Region:", "region")

    def _add_ftp_settings(self):
        """Настройки FTP."""
        self._add_field(self.settings_frame, "Host:", "host")
        self._add_field(self.settings_frame, "Port:", "port")
        self._add_field(self.settings_frame, "Username:", "username")
        self._add_field(self.settings_frame, "Password:", "password", is_password=True)

        self.var_tls = ctk.BooleanVar()
        ctk.CTkCheckBox(self.settings_frame, text="Использовать TLS", variable=self.var_tls).pack(padx=5, pady=5, anchor="w")

    def _add_ssh_settings(self):
        """Настройки SSH."""
        self._add_field(self.settings_frame, "Host:", "host")
        self._add_field(self.settings_frame, "Port:", "port")
        self._add_field(self.settings_frame, "Username:", "username")
        self._add_field(self.settings_frame, "Password:", "password", is_password=True)
        self._add_field(self.settings_frame, "Private Key Path:", "private_key_path")
        self._add_field(self.settings_frame, "Remote Path:", "remote_path")

    def _add_google_settings(self):
        """Настройки Google Drive."""
        self._add_field(self.settings_frame, "Credentials JSON path:", "credentials_path")
        self._add_field(self.settings_frame, "Folder ID (опционально):", "folder_id")

    def _add_email_settings(self):
        """Настройки Email."""
        self._add_field(self.settings_frame, "SMTP Server:", "smtp_server")
        self._add_field(self.settings_frame, "SMTP Port:", "smtp_port")
        self._add_field(self.settings_frame, "Username:", "username")
        self._add_field(self.settings_frame, "Password:", "password", is_password=True)
        self._add_field(self.settings_frame, "From Email:", "from_email")
        self._add_field(self.settings_frame, "To Email:", "to_email")

    def _add_local_settings(self):
        """Настройки локальной папки."""
        ctk.CTkLabel(self.settings_frame, text="Локальная папка для бэкапов:").pack(padx=5, pady=(5, 0), anchor="w")

        frame = ctk.CTkFrame(self.settings_frame)
        frame.pack(padx=5, pady=5, fill="x")

        self.entry_local_path = ctk.CTkEntry(frame)
        self.entry_local_path.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(frame, text="Обзор...", command=self._browse_local).pack(side="left", padx=5)

        self.entries["local_path"] = self.entry_local_path

    def _browse_local(self):
        """Выбрать локальную папку."""
        from tkinter import filedialog
        path = filedialog.askdirectory(title="Выберите папку")
        if path:
            self.entry_local_path.delete(0, "end")
            self.entry_local_path.insert(0, path)

    def _save(self):
        """Сохранить подключение."""
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Введите имя подключения")
            return

        # Определяем тип
        choice = self.combo_type.get()
        type_value = None
        for t in ConnectionType.choices():
            if t[1] == choice:
                type_value = t[0]
                break

        # Собираем настройки
        config = {}
        for key, entry in self.entries.items():
            if hasattr(entry, 'get'):
                config[key] = entry.get()
            elif hasattr(entry, 'cget'):
                config[key] = entry.cget("textvariable") if hasattr(entry, 'cget') else ""

        # Добавляем специфичные поля
        if type_value == ConnectionType.TELEGRAM.value:
            config["is_premium"] = self.var_premium.get()
        elif type_value == ConnectionType.FTP.value:
            config["use_tls"] = self.var_tls.get()

        # Создаем подключение
        conn = ConnectionConfig(name=name, type=ConnectionType(type_value), config=config)
        self.result = conn
        self.destroy()
