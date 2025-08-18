"""Модуль для настройки логирования."""

import os
import logging
import logging.handlers
from typing import Optional


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Настраивает систему логирования.
    
    Args:
        log_level (str): Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str, optional): Путь к файлу логов. Если не указан, логи выводятся только в консоль.
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    # Преобразование строкового уровня логирования в константу
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Базовая конфигурация логгера
    logger = logging.getLogger("agentcli")
    logger.setLevel(numeric_level)
    
    # Очищаем существующие обработчики, если они есть
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
    
    # Формат сообщений логов
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчик для вывода логов в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # Обработчик для записи логов в файл, если указан путь
    if log_file:
        # Создаем директорию для логов, если она не существует
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Настраиваем ротацию логов (максимум 5 файлов по 5 МБ)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5 МБ
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    
    return logger


# Глобальный логгер для всего приложения
logger = setup_logging(
    log_level=os.environ.get("AGENTCLI_LOG_LEVEL", "INFO"),
    log_file=os.environ.get("AGENTCLI_LOG_FILE", os.path.join(os.getcwd(), ".agentcli", "logs", "app.log"))
)
