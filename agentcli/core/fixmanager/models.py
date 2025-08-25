import ast
from pathlib import Path
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class FileContext:
    path: Path
    content: str
    ast_tree: Optional[ast.AST]
    imports: List[str]
    exports: List[str]
    dependencies: Set[str]
    dependents: Set[str]
    complexity_score: int
    last_modified: datetime
    line_count: int

@dataclass
class ModuleContext:
    name: str
    path: Path
    files: List[FileContext]
    submodules: List['ModuleContext']
    public_api: List[str]
    internal_dependencies: Set[str]
    external_dependencies: Set[str]

@dataclass
class ProjectContext:
    root_path: Path
    modules: Dict[str, ModuleContext]
    dependency_graph: Dict[str, Set[str]]
    import_map: Dict[str, str]
    global_symbols: Dict[str, str]
    architecture_patterns: List[str]
    config_files: List[Path]
    test_files: List[Path]