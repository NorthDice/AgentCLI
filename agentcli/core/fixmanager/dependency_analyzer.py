import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict

from .models import FileContext

class DependencyAnalyzer:
    """Dependency analyzer between files and modules."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.import_patterns = [
            r'^from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import\s+(.+)$',
            r'^import\s+([a-zA-Z_][a-zA-Z0-9_.]*(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_.]*)*)$',
        ]
    
    def analyze_file_imports(self, file_path: Path, content: str) -> Tuple[List[str], Set[str]]:
        imports = []
        dependencies = set()
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return imports, dependencies
            
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
                    dep_file = self._resolve_import_to_file(alias.name, file_path)
                    if dep_file:
                        dependencies.add(str(dep_file))
                        
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    import_names = [alias.name for alias in node.names]
                    imports.append(f"from {node.module} import {', '.join(import_names)}")
                    dep_file = self._resolve_import_to_file(node.module, file_path)
                    if dep_file:
                        dependencies.add(str(dep_file))
        
        return imports, dependencies
    
    def _resolve_import_to_file(self, module_name: str, current_file: Path) -> Optional[Path]:
        """Resolves import name to file path."""
        # Relative imports
        if module_name.startswith('.'):
            base_dir = current_file.parent
            module_parts = module_name.lstrip('.').split('.')
            if module_parts == ['']:
                module_parts = []
            
            # Traverse up the hierarchy for each dot
            for _ in range(len(module_name) - len(module_name.lstrip('.'))):
                base_dir = base_dir.parent
                
            target_path = base_dir
            for part in module_parts:
                target_path = target_path / part
                
            # Check different candidates
            candidates = [
                target_path.with_suffix('.py'),
                target_path / '__init__.py',
            ]
            
            for candidate in candidates:
                if candidate.exists() and candidate.is_relative_to(self.root_path):
                    return candidate
        
        # Absolute imports inside the project
        else:
            module_parts = module_name.split('.')
            target_path = self.root_path
            
            for part in module_parts:
                target_path = target_path / part
                
            candidates = [
                target_path.with_suffix('.py'),
                target_path / '__init__.py',
            ]
            
            for candidate in candidates:
                if candidate.exists():
                    return candidate
                    
        return None
    
    def build_dependency_graph(self, files: List[FileContext]) -> Dict[str, Set[str]]:
        graph = defaultdict(set)
        
        for file_ctx in files:
            file_path = str(file_ctx.path)
            graph[file_path] = file_ctx.dependencies.copy()
            
        return dict(graph)
    
    def find_circular_dependencies(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node):
            if node in rec_stack:
                # Найден цикл
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return
                
            if node in visited:
                return
                
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, set()):
                dfs(neighbor)
                
            rec_stack.remove(node)
            path.pop()
            
        for node in graph:
            if node not in visited:
                dfs(node)
                
        return cycles