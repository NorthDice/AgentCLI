"""Utility module for managing tree-sitter parsers."""

import os
import shutil
import subprocess
from pathlib import Path
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Directory for tree-sitter grammar repositories and compiled libraries
PARSERS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")
REPOS_DIR = os.path.join(PARSERS_DIR, "repos")

# Mapping of language names to their repository URLs
LANGUAGE_REPOS = {
    "python": "https://github.com/tree-sitter/tree-sitter-python",
    "javascript": "https://github.com/tree-sitter/tree-sitter-javascript",
    "typescript": "https://github.com/tree-sitter/tree-sitter-typescript",
    "java": "https://github.com/tree-sitter/tree-sitter-java",
    "c": "https://github.com/tree-sitter/tree-sitter-c",
    "cpp": "https://github.com/tree-sitter/tree-sitter-cpp",
    "go": "https://github.com/tree-sitter/tree-sitter-go",
    "ruby": "https://github.com/tree-sitter/tree-sitter-ruby",
    "rust": "https://github.com/tree-sitter/tree-sitter-rust",
}

def check_tree_sitter_installed() -> bool:
    """Check if tree-sitter is installed.
    
    Returns:
        bool: True if tree-sitter is available, False otherwise.
    """
    try:
        import tree_sitter
        return True
    except ImportError:
        return False

def setup_parser_directory() -> None:
    """Set up directories for parser repositories and builds."""
    os.makedirs(PARSERS_DIR, exist_ok=True)
    os.makedirs(REPOS_DIR, exist_ok=True)

def clone_language_repo(language: str) -> bool:
    """Clone a language grammar repository.
    
    Args:
        language: Name of the language to clone.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    if language not in LANGUAGE_REPOS:
        logger.error(f"Unknown language: {language}")
        return False
        
    repo_url = LANGUAGE_REPOS[language]
    repo_dir = os.path.join(REPOS_DIR, f"tree-sitter-{language}")
    
    # Skip if already cloned
    if os.path.exists(repo_dir):
        logger.info(f"Repository for {language} already exists at {repo_dir}")
        return True
        
    try:
        logger.info(f"Cloning {language} grammar from {repo_url}...")
        subprocess.run(
            ["git", "clone", repo_url, repo_dir],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        logger.info(f"Successfully cloned {language} grammar to {repo_dir}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone {language} grammar: {e}")
        return False
    except Exception as e:
        logger.error(f"Error cloning {language} grammar: {str(e)}")
        return False

def build_language_parser(language: str) -> Optional[str]:
    """Build a language parser.
    
    Args:
        language: Name of the language to build.
        
    Returns:
        Optional[str]: Path to the built library or None if failed.
    """
    if not check_tree_sitter_installed():
        logger.error("tree-sitter is not installed. Please install it first.")
        return None
        
    # Ensure directories are set up
    setup_parser_directory()
    
    # Clone the repository if needed
    if not clone_language_repo(language):
        return None
        
    # Path to the repository
    repo_dir = os.path.join(REPOS_DIR, f"tree-sitter-{language}")
    
    # Path for the output library
    lib_path = os.path.join(PARSERS_DIR, f"{language}.so")
    
    try:
        from tree_sitter import Language
        
        # Build the parser
        logger.info(f"Building {language} parser...")
        Language.build_library(
            lib_path,
            [repo_dir]
        )
        
        logger.info(f"Successfully built {language} parser at {lib_path}")
        return lib_path
    except Exception as e:
        logger.error(f"Failed to build {language} parser: {str(e)}")
        return None

def load_language(language: str) -> Optional[object]:
    """Load a language from a built parser.
    
    Args:
        language: Name of the language to load.
        
    Returns:
        Optional[object]: The Language object or None if failed.
    """
    if not check_tree_sitter_installed():
        logger.error("tree-sitter is not installed")
        return None
        
    # Path to the library
    lib_path = os.path.join(PARSERS_DIR, f"{language}.so")
    
    # Build the parser if it doesn't exist
    if not os.path.exists(lib_path):
        lib_path = build_language_parser(language)
        if not lib_path:
            return None
    
    try:
        from tree_sitter import Language
        return Language(lib_path, language)
    except Exception as e:
        logger.error(f"Failed to load {language} parser: {str(e)}")
        return None

def get_parser(language: str) -> Optional[object]:
    """Get a parser for a language.
    
    Args:
        language: Name of the language.
        
    Returns:
        Optional[object]: Parser object or None if failed.
    """
    if not check_tree_sitter_installed():
        logger.error("tree-sitter is not installed")
        return None
        
    try:
        from tree_sitter import Parser
        
        language_obj = load_language(language)
        if not language_obj:
            return None
            
        parser = Parser()
        parser.set_language(language_obj)
        return parser
    except Exception as e:
        logger.error(f"Failed to create parser for {language}: {str(e)}")
        return None

def setup_parsers(languages: List[str] = None) -> Dict[str, object]:
    """Set up parsers for multiple languages.
    
    Args:
        languages: List of languages to set up parsers for.
                  If None, will use all available languages.
                  
    Returns:
        Dict[str, object]: Dictionary mapping language names to parser objects.
    """
    if languages is None:
        languages = list(LANGUAGE_REPOS.keys())
        
    parsers = {}
    for lang in languages:
        parser = get_parser(lang)
        if parser:
            parsers[lang] = parser
            
    return parsers

def install_tree_sitter() -> bool:
    """Attempt to install tree-sitter using pip.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        subprocess.run(
            ["pip", "install", "tree-sitter"],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        logger.info("Successfully installed tree-sitter")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install tree-sitter: {e}")
        return False
