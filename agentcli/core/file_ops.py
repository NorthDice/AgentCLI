"""Модуль для операций с файлами."""

import os
import re
import stat
import shutil
from typing import Optional, Union, List, Pattern, AnyStr, Tuple

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


def get_file_permissions(file_path: str) -> int:
    """Получает права доступа к файлу.
    
    Args:
        file_path (str): Путь к файлу.
        
    Returns:
        int: Права доступа файла.
        
    Raises:
        FileOperationError: Если не удалось получить права доступа.
    """
    try:
        logger.debug(f"Получение прав доступа для файла: {file_path}")
        return os.stat(file_path).st_mode
    except PermissionError as e:
        logger.error(f"Нет прав для получения прав доступа файла: {file_path}")
        raise FileOperationError(f"Нет прав для получения прав доступа файла: {file_path}", 
                                file_path=file_path, operation="get_permissions", cause=e)
    except Exception as e:
        logger.error(f"Ошибка при получении прав доступа файла {file_path}: {str(e)}")
        raise FileOperationError(f"Ошибка при получении прав доступа файла: {str(e)}", 
                                file_path=file_path, operation="get_permissions", cause=e)


def set_file_permissions(file_path: str, permissions: int) -> bool:
    """Устанавливает права доступа файла.
    
    Args:
        file_path (str): Путь к файлу.
        permissions (int): Права доступа для установки.
        
    Returns:
        bool: Успешность операции.
        
    Raises:
        FileOperationError: Если не удалось установить права доступа.
    """
    try:
        logger.debug(f"Установка прав доступа для файла: {file_path}")
        os.chmod(file_path, permissions)
        logger.debug(f"Успешно установлены права доступа для файла: {file_path}")
        return True
    except PermissionError as e:
        logger.error(f"Нет прав для установки прав доступа файла: {file_path}")
        raise FileOperationError(f"Нет прав для установки прав доступа файла: {file_path}", 
                                file_path=file_path, operation="set_permissions", cause=e)
    except Exception as e:
        logger.error(f"Ошибка при установке прав доступа файла {file_path}: {str(e)}")
        raise FileOperationError(f"Ошибка при установке прав доступа файла: {str(e)}", 
                                file_path=file_path, operation="set_permissions", cause=e)


def copy_file_permissions(source_path: str, target_path: str) -> bool:
    """Копирует права доступа с одного файла на другой.
    
    Args:
        source_path (str): Путь к исходному файлу.
        target_path (str): Путь к целевому файлу.
        
    Returns:
        bool: Успешность операции.
        
    Raises:
        FileOperationError: Если не удалось скопировать права доступа.
    """
    try:
        logger.debug(f"Копирование прав доступа с {source_path} на {target_path}")
        permissions = get_file_permissions(source_path)
        set_file_permissions(target_path, permissions)
        logger.debug(f"Успешно скопированы права доступа с {source_path} на {target_path}")
        return True
    except FileOperationError:
        # Пробрасываем исключение выше
        raise
    except Exception as e:
        logger.error(f"Ошибка при копировании прав доступа: {str(e)}")
        raise FileOperationError(f"Ошибка при копировании прав доступа: {str(e)}", 
                                file_path=target_path, operation="copy_permissions", cause=e)


def create_file_if_not_exists(file_path: str, content: str = "", encoding: str = 'utf-8') -> bool:
    """Создает файл только если он не существует.
    
    Args:
        file_path (str): Путь к файлу.
        content (str): Содержимое для записи.
        encoding (str): Кодировка файла.
        
    Returns:
        bool: True если файл был создан, False если файл уже существует.
        
    Raises:
        FileOperationError: Если не удалось создать файл.
    """
    try:
        logger.debug(f"Проверка существования файла: {file_path}")
        
        if os.path.exists(file_path):
            logger.debug(f"Файл уже существует, создание пропущено: {file_path}")
            return False
        
        write_file(file_path, content, encoding)
        logger.debug(f"Файл успешно создан: {file_path}")
        return True
    except FileOperationError:
        # Пробрасываем исключение выше
        raise
    except Exception as e:
        logger.error(f"Ошибка при создании файла {file_path}: {str(e)}")
        raise FileOperationError(f"Ошибка при создании файла: {str(e)}", 
                                file_path=file_path, operation="create_if_not_exists", cause=e)


def append_to_file(file_path: str, content: str, encoding: str = 'utf-8', 
                  create_if_missing: bool = True, preserve_permissions: bool = True) -> bool:
    """Добавляет содержимое в конец файла.
    
    Args:
        file_path (str): Путь к файлу.
        content (str): Содержимое для добавления.
        encoding (str): Кодировка файла.
        create_if_missing (bool): Создавать файл, если он не существует.
        preserve_permissions (bool): Сохранять права доступа файла.
        
    Returns:
        bool: Успешность операции.
        
    Raises:
        FileOperationError: Если не удалось добавить содержимое.
    """
    try:
        logger.debug(f"Добавление содержимого в конец файла: {file_path}")
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            if create_if_missing:
                logger.debug(f"Файл не существует, создаем новый: {file_path}")
                return write_file(file_path, content, encoding)
            else:
                error_msg = f"Файл не существует: {file_path}"
                logger.error(error_msg)
                raise FileOperationError(error_msg, file_path=file_path, operation="append")
        
        # Получаем текущие права доступа, если нужно
        permissions = None
        if preserve_permissions:
            permissions = get_file_permissions(file_path)
        
        # Добавляем содержимое
        try:
            with open(file_path, 'a', encoding=encoding) as f:
                f.write(content)
            
            logger.debug(f"Успешно добавлено содержимое в файл: {file_path}")
            return True
        finally:
            # Восстанавливаем права доступа, если нужно
            if permissions is not None:
                set_file_permissions(file_path, permissions)
    except FileOperationError:
        # Пробрасываем исключение выше
        raise
    except Exception as e:
        logger.error(f"Ошибка при добавлении содержимого в файл {file_path}: {str(e)}")
        raise FileOperationError(f"Ошибка при добавлении содержимого в файл: {str(e)}", 
                                file_path=file_path, operation="append", cause=e)


def insert_into_file(file_path: str, content: str, position: Union[int, str, Pattern[AnyStr]], 
                  before: bool = True, encoding: str = 'utf-8', 
                  create_if_missing: bool = False, preserve_permissions: bool = True) -> bool:
    """Вставляет содержимое в указанное место файла.
    
    Args:
        file_path (str): Путь к файлу.
        content (str): Содержимое для вставки.
        position: Позиция вставки. Может быть номером строки (int), строкой для поиска (str) или регулярным выражением (Pattern).
        before (bool): Вставлять перед указанной позицией (True) или после (False).
        encoding (str): Кодировка файла.
        create_if_missing (bool): Создавать файл, если он не существует.
        preserve_permissions (bool): Сохранять права доступа файла.
        
    Returns:
        bool: Успешность операции.
        
    Raises:
        FileOperationError: Если не удалось вставить содержимое.
    """
    try:
        logger.debug(f"Вставка содержимого в файл: {file_path} на позицию {position}")
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            if create_if_missing:
                logger.debug(f"Файл не существует, создаем новый: {file_path}")
                return write_file(file_path, content, encoding)
            else:
                error_msg = f"Файл не существует: {file_path}"
                logger.error(error_msg)
                raise FileOperationError(error_msg, file_path=file_path, operation="insert")
        
        # Получаем текущие права доступа, если нужно
        permissions = None
        if preserve_permissions:
            permissions = get_file_permissions(file_path)
        
        # Читаем содержимое файла
        with open(file_path, 'r', encoding=encoding) as f:
            lines = f.readlines()
        
        # Определяем позицию для вставки
        insert_index = None
        
        if isinstance(position, int):
            # Позиция - номер строки
            if 1 <= position <= len(lines) + 1:
                insert_index = position - 1  # 0-based index
            else:
                error_msg = f"Некорректный номер строки: {position}, всего строк: {len(lines)}"
                logger.error(error_msg)
                raise FileOperationError(error_msg, file_path=file_path, operation="insert")
        else:
            # Позиция - строка для поиска или регулярное выражение
            pattern_found = False
            for i, line in enumerate(lines):
                if isinstance(position, Pattern):
                    match = position.search(line)
                    if match:
                        insert_index = i
                        pattern_found = True
                        break
                elif position in line:
                    insert_index = i
                    pattern_found = True
                    break
            
            if not pattern_found:
                error_msg = f"Строка/шаблон не найден: {position}"
                logger.error(error_msg)
                raise FileOperationError(error_msg, file_path=file_path, operation="insert")
            
            if not before:
                insert_index += 1
        
        # Добавляем новую строку, убеждаемся, что она заканчивается переводом строки
        new_content = content if content.endswith('\n') else content + '\n'
        lines.insert(insert_index, new_content)
        
        # Записываем обновленное содержимое
        with open(file_path, 'w', encoding=encoding) as f:
            f.writelines(lines)
        
        logger.debug(f"Успешно вставлено содержимое в файл: {file_path} на позицию {position}")
        
        # Восстанавливаем права доступа, если нужно
        if permissions is not None:
            set_file_permissions(file_path, permissions)
        
        return True
    except FileOperationError:
        # Пробрасываем исключение выше
        raise
    except Exception as e:
        logger.error(f"Ошибка при вставке содержимого в файл {file_path}: {str(e)}")
        raise FileOperationError(f"Ошибка при вставке содержимого в файл: {str(e)}", 
                                file_path=file_path, operation="insert", cause=e)


def replace_in_file(file_path: str, pattern: Union[str, Pattern[AnyStr]], replacement: str, 
                   encoding: str = 'utf-8', count: int = 0, preserve_permissions: bool = True) -> Tuple[bool, int]:
    """Заменяет текст в файле по заданному шаблону.
    
    Args:
        file_path (str): Путь к файлу.
        pattern: Строка для поиска (str) или регулярное выражение (Pattern).
        replacement (str): Строка для замены.
        encoding (str): Кодировка файла.
        count (int): Максимальное количество замен. 0 = все совпадения.
        preserve_permissions (bool): Сохранять права доступа файла.
        
    Returns:
        Tuple[bool, int]: (успешность операции, количество замен)
        
    Raises:
        FileOperationError: Если не удалось заменить содержимое.
    """
    try:
        logger.debug(f"Замена содержимого в файле: {file_path}")
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            error_msg = f"Файл не существует: {file_path}"
            logger.error(error_msg)
            raise FileOperationError(error_msg, file_path=file_path, operation="replace")
        
        # Получаем текущие права доступа, если нужно
        permissions = None
        if preserve_permissions:
            permissions = get_file_permissions(file_path)
        
        # Читаем содержимое файла
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        
        # Выполняем замену
        if isinstance(pattern, Pattern):
            if count > 0:
                new_content, num_replacements = re.subn(pattern, replacement, content, count=count)
            else:
                new_content, num_replacements = re.subn(pattern, replacement, content)
        else:
            if count > 0:
                new_content = content.replace(pattern, replacement, count)
                num_replacements = (content.count(pattern) if count > content.count(pattern) else count)
            else:
                num_replacements = content.count(pattern)
                new_content = content.replace(pattern, replacement)
        
        # Если нет изменений, выходим
        if num_replacements == 0:
            logger.debug(f"Строка/шаблон не найден, замены не выполнены: {pattern}")
            return False, 0
        
        # Записываем обновленное содержимое
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(new_content)
        
        logger.debug(f"Успешно заменено {num_replacements} вхождений в файле: {file_path}")
        
        # Восстанавливаем права доступа, если нужно
        if permissions is not None:
            set_file_permissions(file_path, permissions)
        
        return True, num_replacements
    except FileOperationError:
        # Пробрасываем исключение выше
        raise
    except Exception as e:
        logger.error(f"Ошибка при замене содержимого в файле {file_path}: {str(e)}")
        raise FileOperationError(f"Ошибка при замене содержимого в файле: {str(e)}", 
                                file_path=file_path, operation="replace", cause=e)
