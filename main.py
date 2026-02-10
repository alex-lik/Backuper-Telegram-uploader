"""
Backuper Telegram Uploader
Приложение для создания бэкапов с выгрузкой в различные хранилища.
"""

import sys
from src.gui.main_window import MainWindow


def main():
    """Точка входа в приложение."""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
