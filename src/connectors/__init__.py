"""Коннекторы для различных хранилищ."""

from .base import BaseConnector
from .local import LocalConnector
from .telegram import TelegramConnector

__all__ = ["BaseConnector", "LocalConnector", "TelegramConnector"]
