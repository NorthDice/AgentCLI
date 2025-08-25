"""
Enhanced search functionality with filename matching.
"""

import os
import fnmatch
from typing import List, Dict, Any
from pathlib import Path

from agentcli.core.search import perform_semantic_search, search_files


def enhanced_search(query: str, path: str = ".", semantic: bool = False, max_results: int = 100) -> List[Dict[str, Any]]:

    results = []

    filename_results = search_by_filename(query, path)
    for result in filename_results:
        result['match_type'] = 'filename'
        results.append(result)

    semantic_limit = min(max_results, 10)
    semantic_results = perform_semantic_search(query, path, top_k=semantic_limit)
    semantic_chunks = []
    if semantic_results and 'results' in semantic_results:
        for result in semantic_results['results']:
            metadata = result.get('metadata', {})
            file_path = metadata.get('file_path', result.get('file_path', result.get('file', '')))
            if os.path.isabs(file_path):
                file_path = os.path.relpath(file_path, path)
            elif file_path.startswith('./'):
                file_path = file_path[2:]
            content = result.get('content', result.get('text', ''))
            score = result.get('relevance', result.get('score', 0.0))
            if score < 0:
                score = abs(score)
            elif score > 1:
                score = 1.0 / (1.0 + score)
            chunk_type = metadata.get('chunk_type', '')
            boost = 0.2 if chunk_type == 'function' else 0.0
            semantic_chunks.append({
                'file': file_path,
                'line': metadata.get('start_line', result.get('line_number', 1)),
                'content': content,
                'score': score + boost,
                'match_type': 'semantic',
                'function_name': metadata.get('function_name', ''),
                'chunk_type': chunk_type
            })

    text_results = search_files(
        query=query,
        path=path,
        file_pattern="*",
        is_regex=False,
        case_sensitive=False
    )
    text_chunks = []
    for result in text_results:
        file_path = result.get('file', '')
        if file_path.startswith('./'):
            file_path = file_path[2:]
        matches = result.get('matches', [])
        for match in matches:
            line_num = match.get('line_num', 1)
            line_content = match.get('line', '')
            text_chunks.append({
                'file': file_path,
                'line': line_num,
                'content': line_content,
                'score': 1.0,
                'match_type': 'text',
                'function_name': '',
                'chunk_type': ''
            })


    all_results = results + semantic_chunks + text_chunks
    all_results = deduplicate_results(all_results)
    all_results = [r for r in all_results if not should_ignore_file(r.get('file', ''))]

    def sort_key(result):
        match_type = result['match_type']
        score = result.get('score', 0.0)
        is_function = result.get('chunk_type', '') == 'function'
        if match_type == 'filename':
            return (3, score)
        elif match_type == 'semantic' and is_function:
            return (2, score)
        elif match_type == 'semantic':
            return (1, score)
        else:
            return (0, score)

    all_results = sorted(all_results, key=sort_key, reverse=True)
    return all_results[:max_results]


def should_ignore_file(file_path: str) -> bool:
    """Check if file should be ignored in search results."""
    ignore_patterns = ['.agentcli/', '__pycache__/', '.git/', '.pytest_cache/', 
                      '.mypy_cache/', '.tox/', '.venv/', 'venv/', 'env/', '.env/']
    
    normalized_path = file_path.replace('\\', '/')
    for pattern in ignore_patterns:
        if pattern in normalized_path:
            return True
    
    # Check for cache file extensions
    if file_path.endswith(('.json', '.cache', '.tmp', '.temp')) and '.agentcli' in file_path:
        return True
    
    return False


def search_by_filename(query: str, path: str) -> List[Dict[str, Any]]:
    """Search for files by filename pattern.
    
    Args:
        query: Search query (will be used as filename pattern)
        path: Base path for search
        
    Returns:
        List of matching files
    """
    results = []
    search_pattern = f"*{query}*"
    
    # Walk through directory
    for root, dirs, files in os.walk(path):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if not should_ignore_dir(d)]
        
        for file in files:
            if fnmatch.fnmatch(file.lower(), search_pattern.lower()):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, path)
                
                results.append({
                    'file': rel_path,
                    'line': 1,
                    'content': f"File: {file}",
                    'score': 1.0,
                    'match_type': 'filename'
                })
    
    return results


def should_ignore_dir(dirname: str) -> bool:
    """Check if directory should be ignored."""
    ignore_dirs = {'.git', '__pycache__', '.agentcli', '.pytest_cache', 
                   '.mypy_cache', '.tox', '.venv', 'venv', 'env', '.env',
                   'node_modules', '.eggs', 'dist', 'build'}
    return dirname in ignore_dirs


def deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate results based on file path.
    
    Args:
        results: List of search results
        
    Returns:
        Deduplicated list of results
    """
    seen_files = set()
    deduplicated = []
    
    for result in results:
        file_path = result.get('file', '')
        if file_path not in seen_files:
            seen_files.add(file_path)
            deduplicated.append(result)
    
    return deduplicated


def format_enhanced_results(results: List[Dict[str, Any]], query: str) -> str:
    """Format enhanced search results for display.
    
    Args:
        results: List of search results
        query: Original search query
        
    Returns:
        Formatted string for display
    """
    if not results:
        return f"No results found for '{query}'."
    
    output = []
    output.append(f"\nFound: {len(results)} matches")
    
    # Group by match type
    filename_matches = [r for r in results if r['match_type'] == 'filename']
    content_matches = [r for r in results if r['match_type'] != 'filename']
    
    if filename_matches:
        output.append(f"\n📁 Filename matches ({len(filename_matches)}):")
        for result in filename_matches:
            output.append(f"  {result['file']}")
    
    if content_matches:
        semantic_matches = [r for r in content_matches if r['match_type'] == 'semantic']
        text_matches = [r for r in content_matches if r['match_type'] == 'text']
        
        if semantic_matches:
            output.append(f"\n🧠 Semantic matches ({len(semantic_matches)}):")
            for i, result in enumerate(semantic_matches[:5], 1):  # Top 5 semantic results
                score = result.get('score', 0.0)
                score_text = f" (relevance: {score:.3f})" if score else ""
                output.append(f"  {i}. 📄 {result['file']}:{result.get('line', 1)}{score_text}")
                
                if result.get('content'):
                    # Clean and truncate content
                    content = result['content'].strip()
                    if len(content) > 150:
                        content = content[:150] + "..."
                    # Remove excessive whitespace
                    content = ' '.join(content.split())
                    output.append(f"     {content}")
                output.append("")  # Empty line for readability
        
        if text_matches:
            output.append(f"\n🔍 Text matches ({len(text_matches)}):")
            for result in text_matches[:5]:  # Top 5 text results
                output.append(f"  📄 {result['file']}:{result.get('line', 1)}")
                if result.get('content'):
                    content = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
                    output.append(f"    {content}")
    
    return "\n".join(output)
