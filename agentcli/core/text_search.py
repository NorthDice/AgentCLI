"""Module for basic text search functionality."""

import os
import re
import glob
import fnmatch
from pathlib import Path
from typing import List, Dict, Any, Set, Optional, Union, Pattern as RegexPattern


def get_gitignore_patterns(base_path: str = ".") -> List[str]:
    """Gets patterns from a .gitignore file.
    
    Args:
        base_path (str): Base path to look for .gitignore.
        
    Returns:
        List[str]: List of patterns from .gitignore.
    """
    gitignore_path = os.path.join(base_path, ".gitignore")
    patterns = []
    
    if os.path.isfile(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    patterns.append(line)
    
    return patterns


def should_ignore_file(file_path: str, ignore_patterns: List[str]) -> bool:
    """Checks whether a file should be ignored according to patterns.
    
    Args:
        file_path (str): Path to the file.
        ignore_patterns (List[str]): Patterns to ignore.
        
    Returns:
        bool: True if the file should be ignored, otherwise False.
    """
    # Normalize the path
    norm_path = os.path.normpath(file_path).replace(os.sep, '/')
    
    # Remove leading ./ if present
    if norm_path.startswith('./'):
        norm_path = norm_path[2:]
    
    # Check if this is a directory
    is_directory = os.path.isdir(file_path)
    
    # Split path into components
    path_components = norm_path.split('/')
    filename = path_components[-1]
    
    for pattern in ignore_patterns:
        # Normalize the pattern
        norm_pattern = pattern.replace(os.sep, '/')
        
        # If pattern ends with /, it only applies to directories
        if norm_pattern.endswith('/'):
            if not is_directory:
                continue  # Skip this pattern for files
            # Strip the trailing / for directory matching
            norm_pattern = norm_pattern.rstrip('/')
        
        # Strip leading slashes
        norm_pattern = norm_pattern.lstrip('/')
        
        # Check for exact matches vs glob patterns
        if '*' in norm_pattern or '?' in norm_pattern:
            # This is a glob pattern
            # Use fnmatch for filename patterns
            if '/' not in norm_pattern:
                # Pattern applies to filename only
                if fnmatch.fnmatch(filename, norm_pattern):
                    return True
            else:
                # Pattern applies to full path
                if fnmatch.fnmatch(norm_path, norm_pattern):
                    return True
        else:
            # This is an exact match pattern
            if '/' in norm_pattern:
                # Pattern specifies path components
                if norm_path == norm_pattern or norm_path.startswith(norm_pattern + '/'):
                    return True
            else:
                # Pattern applies to any file/directory with this name
                if filename == norm_pattern or norm_pattern in path_components:
                    return True
    
    return False


def search_files(
    query: str, 
    path: str = ".", 
    file_pattern: str = "*", 
    ignore_patterns: Optional[List[str]] = None,
    is_regex: bool = False,
    use_gitignore: bool = True,
    case_sensitive: bool = False
) -> List[Dict[str, Any]]:
    """Performs file search.
    
    Args:
        query (str): String or regex to search for.
        path (str): Base path for search.
        file_pattern (str): Pattern to filter files.
        ignore_patterns (List[str]): Patterns to ignore.
        is_regex (bool): Whether to use query as a regex.
        use_gitignore (bool): Whether to use patterns from .gitignore.
        case_sensitive (bool): Whether to consider case in search.
    
    Returns:
        List[Dict[str, Any]]: List of search results.
    """
    if ignore_patterns is None:
        ignore_patterns = [
            ".git", "__pycache__", "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dll", 
            "*.exe", ".env", ".venv", "env", "venv"
        ]
    
    # If use_gitignore flag is set, add patterns from .gitignore
    if use_gitignore:
        gitignore_patterns = get_gitignore_patterns(path)
        if gitignore_patterns:
            ignore_patterns.extend(gitignore_patterns)
    
    # Compile regex if applicable
    regex_pattern = None
    if is_regex:
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            regex_pattern = re.compile(query, flags)
        except re.error:
            # If regex compilation fails, use simple search
            is_regex = False
    
    results = []
    
    # Recursive file search
    for root, dirs, files in os.walk(path):
        # Exclude ignored directories
        dirs[:] = [d for d in dirs if not should_ignore_file(os.path.join(root, d), ignore_patterns)]
        
        # Search in files
        for file in files:
            file_path = os.path.join(root, file)
            
            # Skip ignored files
            if should_ignore_file(file_path, ignore_patterns):
                continue
            
            # Check file name pattern
            if not fnmatch.fnmatch(file, file_pattern):
                continue
            
            try:
                # Check if file is text
                with open(file_path, 'rb') as f:
                    content = f.read(1024)
                    
                    # Skip binary files
                    if b'\0' in content:
                        continue
                
                # Open as text and search
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    line_num = 0
                    matches = []
                    
                    for line in f:
                        line_num += 1
                        
                        if is_regex and regex_pattern:
                            # Regex search
                            for match in regex_pattern.finditer(line):
                                matches.append({
                                    "line_num": line_num,
                                    "line": line.rstrip(),
                                    "match_index": match.start(),
                                    "match_length": match.end() - match.start(),
                                    "match_text": match.group(0)
                                })
                        else:
                            # Simple text search
                            if case_sensitive:
                                if query in line:
                                    matches.append({
                                        "line_num": line_num,
                                        "line": line.rstrip(),
                                        "match_index": line.find(query),
                                        "match_length": len(query),
                                        "match_text": query
                                    })
                            else:
                                lower_line = line.lower()
                                lower_query = query.lower()
                                if lower_query in lower_line:
                                    idx = lower_line.find(lower_query)
                                    matches.append({
                                        "line_num": line_num,
                                        "line": line.rstrip(),
                                        "match_index": idx,
                                        "match_length": len(query),
                                        "match_text": line[idx:idx+len(query)]
                                    })
                    
                    if matches:
                        results.append({
                            "file": file_path,
                            "matches": matches
                        })
            except Exception:
                # Skip files that cannot be read
                continue
    
    return results


def format_search_results(results: List[Dict[str, Any]], format_type: str = "normal", base_path: str = None) -> str:
    """Formats search results into different output styles.
    
    Args:
        results (List[Dict[str, Any]]): Search results.
        format_type (str): Output format (normal, compact, links).
        base_path (str): Base path for relative paths.
    
    Returns:
        str: Formatted search results.
    """
    if not results:
        return "Nothing found."
    
    total_matches = sum(len(result["matches"]) for result in results)
    
    if base_path is None:
        base_path = os.getcwd()
    
    output = []
    
    if format_type == "links":
        # file:line link format
        output.append(f"Found {total_matches} matches in {len(results)} files:\n")
        
        for file_result in results:
            file_path = file_result["file"]
            rel_path = os.path.relpath(file_path, base_path)
            
            for match in file_result["matches"]:
                line_num = match["line_num"]
                output.append(f"{rel_path}:{line_num}: {match['line'].strip()}")
    
    elif format_type == "compact":
        # Compact format
        output.append(f"Found {total_matches} matches in {len(results)} files:\n")
        
        for file_result in results:
            file_path = file_result["file"]
            rel_path = os.path.relpath(file_path, base_path)
            matches = [str(match["line_num"]) for match in file_result["matches"]]
            
            output.append(f"{rel_path} (lines: {', '.join(matches)})")
    
    else:  # normal
        # Normal format
        output.append(f"Found {total_matches} matches in {len(results)} files:\n")
        
        for file_result in results:
            file_path = file_result["file"]
            rel_path = os.path.relpath(file_path, base_path)
            
            output.append(f"\n{rel_path}:")
            
            for match in file_result["matches"]:
                line_num = match["line_num"]
                line = match["line"].rstrip()
                output.append(f"  {line_num}: {line}")
    
    return "\n".join(output)
