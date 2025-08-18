"""Module for file operations."""

import os
import re
import stat
import shutil
from typing import Optional, Union, List, Pattern, AnyStr, Tuple

from agentcli.core.exceptions import FileOperationError
from agentcli.utils.logging import logger


def read_file(file_path: str, encoding: str = 'utf-8', errors: str = 'strict') -> str:
    """Reads the contents of a file.
    
    Args:
        file_path (str): Path to the file.
        encoding (str): File encoding.
        errors (str): Error handling for encoding issues.
        
    Returns:
        str: File contents.
        
    Raises:
        FileOperationError: If the file is not found or cannot be read.
    """
    try:
        logger.debug(f"Reading file: {file_path}")
        with open(file_path, 'r', encoding=encoding, errors=errors) as f:
            content = f.read()
        logger.debug(f"Successfully read file: {file_path}, size: {len(content)} bytes")
        return content
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}")
        raise FileOperationError(f"File not found: {file_path}", file_path=file_path, operation="read", cause=e)
    except PermissionError as e:
        logger.error(f"No permission to read file: {file_path}")
        raise FileOperationError(f"No permission to read file: {file_path}", file_path=file_path, operation="read", cause=e)
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        raise FileOperationError(f"Error reading file: {str(e)}", file_path=file_path, operation="read", cause=e)


def write_file(file_path: str, content: str, encoding: str = 'utf-8', make_dirs: bool = True) -> bool:
    """Writes content to a file.
    
    Args:
        file_path (str): Path to the file.
        content (str): Content to write.
        encoding (str): File encoding.
        make_dirs (bool): Create parent directories if they do not exist.
        
    Returns:
        bool: Success of the operation.
        
    Raises:
        FileOperationError: If unable to write to the file.
    """
    try:
        logger.debug(f"Writing to file: {file_path}")
        
        if make_dirs and os.path.dirname(file_path):
            dir_path = os.path.dirname(file_path)
            os.makedirs(dir_path, exist_ok=True)
            logger.debug(f"Directory created: {dir_path}")
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        logger.debug(f"Successfully wrote to file: {file_path}, size: {len(content)} bytes")
        return True
    except PermissionError as e:
        logger.error(f"No permission to write to file: {file_path}")
        raise FileOperationError(f"No permission to write to file: {file_path}", file_path=file_path, operation="write", cause=e)
    except Exception as e:
        logger.error(f"Error writing to file {file_path}: {str(e)}")
        raise FileOperationError(f"Error writing to file: {str(e)}", file_path=file_path, operation="write", cause=e)


def delete_file(file_path: str, check_exists: bool = True) -> bool:
    """Deletes a file.
    
    Args:
        file_path (str): Path to the file.
        check_exists (bool): Check for file existence before deleting.
        
    Returns:
        bool: Success of the operation.
        
    Raises:
        FileOperationError: If unable to delete the file.
    """
    try:
        logger.debug(f"Deleting file: {file_path}")
        
        if check_exists and not os.path.exists(file_path):
            logger.warning(f"File does not exist for deletion: {file_path}")
            return False
        
        os.remove(file_path)
        logger.debug(f"Successfully deleted file: {file_path}")
        return True
    except PermissionError as e:
        logger.error(f"No permission to delete file: {file_path}")
        raise FileOperationError(f"No permission to delete file: {file_path}", file_path=file_path, operation="delete", cause=e)
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")
        raise FileOperationError(f"Error deleting file: {str(e)}", file_path=file_path, operation="delete", cause=e)


def get_file_permissions(file_path: str) -> int:
    """Gets the permissions of a file.
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        int: File permissions.
        
    Raises:
        FileOperationError: If unable to get file permissions.
    """
    try:
        logger.debug(f"Getting file permissions for: {file_path}")
        return os.stat(file_path).st_mode
    except PermissionError as e:
        logger.error(f"No permission to get file permissions: {file_path}")
        raise FileOperationError(f"No permission to get file permissions: {file_path}", 
                                file_path=file_path, operation="get_permissions", cause=e)
    except Exception as e:
        logger.error(f"Error getting file permissions {file_path}: {str(e)}")
        raise FileOperationError(f"Error getting file permissions: {str(e)}", 
                                file_path=file_path, operation="get_permissions", cause=e)


def set_file_permissions(file_path: str, permissions: int) -> bool:
    """Sets the permissions of a file.
    
    Args:
        file_path (str): Path to the file.
        permissions (int): Permissions to set.
        
    Returns:
        bool: Success of the operation.
        
    Raises:
        FileOperationError: If unable to set file permissions.
    """
    try:
        logger.debug(f"Setting file permissions for: {file_path}")
        os.chmod(file_path, permissions)
        logger.debug(f"Successfully set file permissions for: {file_path}")
        return True
    except PermissionError as e:
        logger.error(f"No permission to set file permissions: {file_path}")
        raise FileOperationError(f"No permission to set file permissions: {file_path}", 
                                file_path=file_path, operation="set_permissions", cause=e)
    except Exception as e:
        logger.error(f"Error setting file permissions {file_path}: {str(e)}")
        raise FileOperationError(f"Error setting file permissions: {str(e)}", 
                                file_path=file_path, operation="set_permissions", cause=e)


def copy_file_permissions(source_path: str, target_path: str) -> bool:
    """Copies file permissions from one file to another.
    
    Args:
        source_path (str): Source file path.
        target_path (str): Target file path.
        
    Returns:
        bool: Success of the operation.
        
    Raises:
        FileOperationError: If unable to copy file permissions.
    """
    try:
        logger.debug(f"Copying file permissions from {source_path} to {target_path}")
        permissions = get_file_permissions(source_path)
        set_file_permissions(target_path, permissions)
        logger.debug(f"Successfully copied file permissions from {source_path} to {target_path}")
        return True
    except FileOperationError:
        raise
    except Exception as e:
        logger.error(f"Error copying file permissions: {str(e)}")
        raise FileOperationError(f"Error copying file permissions: {str(e)}", 
                                file_path=target_path, operation="copy_permissions", cause=e)


def create_file_if_not_exists(file_path: str, content: str = "", encoding: str = 'utf-8') -> bool:
    """Creates a file only if it does not exist.
    
    Args:
        file_path (str): Path to the file.
        content (str): Content to write.
        encoding (str): File encoding.
        
    Returns:
        bool: True if file was created, False if file already exists.
        
    Raises:
        FileOperationError: If unable to create the file.
    """
    try:
        logger.debug(f"Checking file existence: {file_path}")
        
        if os.path.exists(file_path):
            logger.debug(f"File already exists, skipping creation: {file_path}")
            return False
        
        write_file(file_path, content, encoding)
        logger.debug(f"File successfully created: {file_path}")
        return True
    except FileOperationError:
        raise
    except Exception as e:
        logger.error(f"Error creating file {file_path}: {str(e)}")
        raise FileOperationError(f"Error creating file: {str(e)}", 
                                file_path=file_path, operation="create_if_not_exists", cause=e)


def append_to_file(file_path: str, content: str, encoding: str = 'utf-8', 
                  create_if_missing: bool = True, preserve_permissions: bool = True) -> bool:
    """Appends content to the end of a file.
    
    Args:
        file_path (str): Path to the file.
        content (str): Content to append.
        encoding (str): File encoding.
        create_if_missing (bool): Create the file if it does not exist.
        preserve_permissions (bool): Preserve the file permissions.
        
    Returns:
        bool: Success of the operation.
        
    Raises:
        FileOperationError: If unable to append content.
    """
    try:
        logger.debug(f"Appending content to file: {file_path}")
        
        if not os.path.exists(file_path):
            if create_if_missing:
                logger.debug(f"File does not exist, creating new: {file_path}")
                return write_file(file_path, content, encoding)
            else:
                error_msg = f"File does not exist: {file_path}"
                logger.error(error_msg)
                raise FileOperationError(error_msg, file_path=file_path, operation="append")
        
        permissions = None
        if preserve_permissions:
            permissions = get_file_permissions(file_path)
        
        try:
            with open(file_path, 'a', encoding=encoding) as f:
                f.write(content)
            
            logger.debug(f"Successfully appended content to file: {file_path}")
            return True
        finally:
            if permissions is not None:
                set_file_permissions(file_path, permissions)
    except FileOperationError:
        raise
    except Exception as e:
        logger.error(f"Error appending content to file {file_path}: {str(e)}")
        raise FileOperationError(f"Error appending content to file: {str(e)}", 
                                file_path=file_path, operation="append", cause=e)


def insert_into_file(file_path: str, content: str, position: Union[int, str, Pattern[AnyStr]], 
                  before: bool = True, encoding: str = 'utf-8', 
                  create_if_missing: bool = False, preserve_permissions: bool = True) -> bool:
    """Inserts content at a specific position in a file.
    
    Args:
        file_path (str): Path to the file.
        content (str): Content to insert.
        position: Insertion position (line number int, string, or regex pattern).
        before (bool): Insert before (True) or after (False) the position.
        encoding (str): File encoding.
        create_if_missing (bool): Create file if it does not exist.
        preserve_permissions (bool): Preserve file permissions.
        
    Returns:
        bool: Success of the operation.
        
    Raises:
        FileOperationError: If unable to insert content.
    """
    try:
        logger.debug(f"Inserting content into file: {file_path} at position {position}")
        
        if not os.path.exists(file_path):
            if create_if_missing:
                logger.debug(f"File does not exist, creating new: {file_path}")
                return write_file(file_path, content, encoding)
            else:
                error_msg = f"File does not exist: {file_path}"
                logger.error(error_msg)
                raise FileOperationError(error_msg, file_path=file_path, operation="insert")
        
        permissions = None
        if preserve_permissions:
            permissions = get_file_permissions(file_path)
        
        with open(file_path, 'r', encoding=encoding) as f:
            lines = f.readlines()
        
        insert_index = None
        
        if isinstance(position, int):
            if 1 <= position <= len(lines) + 1:
                insert_index = position - 1
            else:
                error_msg = f"Invalid line number: {position}, total lines: {len(lines)}"
                logger.error(error_msg)
                raise FileOperationError(error_msg, file_path=file_path, operation="insert")
        else:
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
                error_msg = f"String/pattern not found: {position}"
                logger.error(error_msg)
                raise FileOperationError(error_msg, file_path=file_path, operation="insert")
            
            if not before:
                insert_index += 1
        
        new_content = content if content.endswith('\n') else content + '\n'
        lines.insert(insert_index, new_content)
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.writelines(lines)
        
        logger.debug(f"Successfully inserted content into file: {file_path} at position {position}")
        
        if permissions is not None:
            set_file_permissions(file_path, permissions)
        
        return True
    except FileOperationError:
        raise
    except Exception as e:
        logger.error(f"Error inserting content into file {file_path}: {str(e)}")
        raise FileOperationError(f"Error inserting content into file: {str(e)}", 
                                file_path=file_path, operation="insert", cause=e)


def replace_in_file(file_path: str, pattern: Union[str, Pattern[AnyStr]], replacement: str, 
                   encoding: str = 'utf-8', count: int = 0, preserve_permissions: bool = True) -> Tuple[bool, int]:
    """Replaces text in a file using a pattern.
    
    Args:
        file_path (str): Path to the file.
        pattern: Search string (str) or regex pattern (Pattern).
        replacement (str): Replacement string.
        encoding (str): File encoding.
        count (int): Maximum number of replacements. 0 = all occurrences.
        preserve_permissions (bool): Preserve file permissions.
        
    Returns:
        Tuple[bool, int]: (success, number of replacements)
        
    Raises:
        FileOperationError: If unable to replace content.
    """
    try:
        logger.debug(f"Replacing content in file: {file_path}")
        
        if not os.path.exists(file_path):
            error_msg = f"File does not exist: {file_path}"
            logger.error(error_msg)
            raise FileOperationError(error_msg, file_path=file_path, operation="replace")
        
        permissions = None
        if preserve_permissions:
            permissions = get_file_permissions(file_path)
        
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        
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
        
        if num_replacements == 0:
            logger.debug(f"String/pattern not found, no replacements made: {pattern}")
            return False, 0
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(new_content)
        
        logger.debug(f"Successfully replaced {num_replacements} occurrences in file: {file_path}")
        
        if permissions is not None:
            set_file_permissions(file_path, permissions)
        
        return True, num_replacements
    except FileOperationError:
        raise
    except Exception as e:
        logger.error(f"Error replacing content in file {file_path}: {str(e)}")
        raise FileOperationError(f"Error replacing content in file: {str(e)}", 
                                file_path=file_path, operation="replace", cause=e)
