#!/usr/bin/env python
"""Script to build and install tree-sitter parsers for code chunking."""

import argparse
import sys
import logging
from agentcli.core.search.parsers.utils import (
    check_tree_sitter_installed,
    install_tree_sitter,
    setup_parser_directory,
    clone_language_repo,
    build_language_parser,
    LANGUAGE_REPOS
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("build_parsers")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Build and install tree-sitter parsers for code chunking."
    )
    
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install tree-sitter if not already installed."
    )
    
    parser.add_argument(
        "--languages",
        nargs="+",
        choices=list(LANGUAGE_REPOS.keys()) + ["all"],
        default=["python"],
        help="Languages to build parsers for. Use 'all' for all supported languages."
    )
    
    args = parser.parse_args()
    
    # Check tree-sitter installation
    if not check_tree_sitter_installed():
        logger.warning("tree-sitter is not installed.")
        if args.install:
            logger.info("Installing tree-sitter...")
            if not install_tree_sitter():
                logger.error("Failed to install tree-sitter. Please install manually.")
                sys.exit(1)
        else:
            logger.error("tree-sitter is required. Use --install to install automatically.")
            sys.exit(1)
    
    # Set up parser directory
    setup_parser_directory()
    
    # Determine languages to build
    languages_to_build = list(LANGUAGE_REPOS.keys()) if "all" in args.languages else args.languages
    
    # Build parsers
    successful = []
    failed = []
    
    for language in languages_to_build:
        logger.info(f"Building parser for {language}...")
        if build_language_parser(language):
            successful.append(language)
        else:
            failed.append(language)
    
    # Print summary
    logger.info("\n=== Build Summary ===")
    logger.info(f"Successfully built parsers for: {', '.join(successful) or 'None'}")
    if failed:
        logger.warning(f"Failed to build parsers for: {', '.join(failed)}")
    
    if failed:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
