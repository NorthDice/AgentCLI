"""Модуль для настройки логирования."""

import os
import logging
import logging.handlers
from typing import Optional


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    

    logger = logging.getLogger("agentcli")
    logger.setLevel(numeric_level)
    

    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
    

    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    

    if log_file:

        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5 МБ
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    
    return logger


logger = setup_logging(
    log_level=os.environ.get("AGENTCLI_LOG_LEVEL", "INFO"),
    log_file=os.environ.get("AGENTCLI_LOG_FILE", os.path.join(os.getcwd(), ".agentcli", "logs", "app.log"))
)
