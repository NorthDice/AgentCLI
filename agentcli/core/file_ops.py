"""Модуль для операций с файлами."""

import os
import shutil
from typing import Optional, Union, List

from agentcli.core.exceptions import FileOperationError
from agentcli.utils.logging import logger


def read_file(file_path: str, encoding: str = 'utf-8', errors: str = 'strict') -> str:
    """Читает содержимое файла.
    
    Args:
        file_path (str): Путь к файлу.
        encoding (str): Кодировка файла.
        errors (str): Обработка ошибок кодирования.
        
    Returns:
        str: Содержимое файла.
        
    Raises:
        FileOperationError: Если файл не найден или не может быть прочитан.
    """
    try:
        logger.debug(f"Чтение файла: {file_path}")
        with open(file_path, 'r', encoding=encoding, errors=errors) as f:
            content = f.read()
        logger.debug(f"Успешно прочитан файл: {file_path}, размер: {len(content)} байт")
        return content
    except FileNotFoundError as e:
        logger.error(f"Файл не найден: {file_path}")
        raise FileOperationError(f"Файл не найден: {file_path}", file_path=file_path, operation="read", cause=e)
    except PermissionError as e:
        logger.error(f"Нет прав для чтения файла: {file_path}")
        raise FileOperationError(f"Нет прав для чтения файла: {file_path}", file_path=file_path, operation="read", cause=e)
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {file_path}: {str(e)}")
        raise FileOperationError(f"Ошибка при чтении файла: {str(e)}", file_path=file_path, operation="read", cause=e)


def write_file(file_path: str, content: str, encoding: str = 'utf-8', make_dirs: bool = True) -> bool:
    """Записывает содержимое в файл.
    
    Args:
        file_path (str): Путь к файлу.
        content (str): Содержимое для записи.
        encoding (str): Кодировка файла.
        make_dirs (bool): Создавать родительские директории, если они не существуют.
        
    Returns:
        bool: Успешность операции.
        
    Raises:
        FileOperationError: Если не удалось записать в файл.
    """
    try:
        logger.debug(f"Запись в файл: {file_path}")
        
        # Создаем родительские директории, если нужно
        if make_dirs and os.path.dirname(file_path):
            dir_path = os.path.dirname(file_path)
            os.makedirs(dir_path, exist_ok=True)
            logger.debug(f"Создана директория: {dir_path}")
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        logger.debug(f"Успешно записано в файл: {file_path}, размер: {len(content)} байт")
        return True
    except PermissionError as e:
        logger.error(f"Нет прав для записи в файл: {file_path}")
        raise FileOperationError(f"Нет прав для записи в файл: {file_path}", file_path=file_path, operation="write", cause=e)
    except Exception as e:
        logger.error(f"Ошибка при записи в файл {file_path}: {str(e)}")
        raise FileOperationError(f"Ошибка при записи в файл: {str(e)}", file_path=file_path, operation="write", cause=e)


def delete_file(file_path: str, check_exists: bool = True) -> bool:
    """Удаляет файл.
    
    Args:
        file_path (str): Путь к файлу.
        check_exists (bool): Проверять существование файла перед удалением.
        
    Returns:
        bool: Успешность операции.
        
    Raises:
        FileOperationError: Если не удалось удалить файл.
    """
    try:
        logger.debug(f"Удаление файла: {file_path}")
        
        if check_exists and not os.path.exists(file_path):
            logger.warning(f"Файл для удаления не существует: {file_path}")
            return False
        
        os.remove(file_path)
        logger.debug(f"Успешно удален файл: {file_path}")
        return True
    except PermissionError as e:
        logger.error(f"Нет прав для удаления файла: {file_path}")
        raise FileOperationError(f"Нет прав для удаления файла: {file_path}", file_path=file_path, operation="delete", cause=e)
    except Exception as e:
        logger.error(f"Ошибка при удалении файла {file_path}: {str(e)}")
        raise FileOperationError(f"Ошибка при удалении файла: {str(e)}", file_path=file_path, operation="delete", cause=e)
