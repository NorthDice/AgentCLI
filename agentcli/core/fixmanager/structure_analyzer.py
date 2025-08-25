import ast
from pathlib import Path
from typing import List, Optional, Set, Tuple
from datetime import datetime

from .models import FileContext, ModuleContext
from .dependency_analyzer import DependencyAnalyzer

class ModuleStructureAnalyzer:
    """Module structure and architecture pattern analyzer."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        
    def analyze_module_structure(self, module_path: Path) -> ModuleContext:
        files = []
        submodules = []
        
        if module_path.is_file() and module_path.suffix == '.py':
            # Одиночный файл
            file_ctx = self._analyze_single_file(module_path)
            if file_ctx:
                files.append(file_ctx)
        elif module_path.is_dir():
            # Пакет
            for item in module_path.iterdir():
                if item.is_file() and item.suffix == '.py':
                    file_ctx = self._analyze_single_file(item)
                    if file_ctx:
                        files.append(file_ctx)
                elif item.is_dir() and (item / '__init__.py').exists():
                    submodule = self.analyze_module_structure(item)
                    submodules.append(submodule)
        
        # Определяем публичное API
        public_api = self._extract_public_api(files)
        
        # Анализируем зависимости
        internal_deps, external_deps = self._analyze_module_dependencies(files)
        
        module_name = module_path.name
        if module_path.suffix == '.py':
            module_name = module_path.stem
            
        return ModuleContext(
            name=module_name,
            path=module_path,
            files=files,
            submodules=submodules,
            public_api=public_api,
            internal_dependencies=internal_deps,
            external_dependencies=external_deps
        )
    
    def _analyze_single_file(self, file_path: Path) -> Optional[FileContext]:
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            return None
            
        try:
            tree = ast.parse(content)
        except SyntaxError:
            tree = None
            
        # Анализируем импорты
        analyzer = DependencyAnalyzer(self.root_path)
        imports, dependencies = analyzer.analyze_file_imports(file_path, content)
        
        # Извлекаем экспорты (функции, классы, переменные)
        exports = self._extract_exports(tree) if tree else []
        
        # Вычисляем сложность
        complexity = self._calculate_complexity(tree) if tree else 0
        
        # Находим dependents (будет заполнено позже)
        dependents = set()
        
        return FileContext(
            path=file_path,
            content=content,
            ast_tree=tree,
            imports=imports,
            exports=exports,
            dependencies=dependencies,
            dependents=dependents,
            complexity_score=complexity,
            last_modified=datetime.fromtimestamp(file_path.stat().st_mtime),
            line_count=len(content.splitlines())
        )
    
    def _extract_exports(self, tree: ast.AST) -> List[str]:
        exports = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith('_'):
                    exports.append(f"function:{node.name}")
            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith('_'):
                    exports.append(f"class:{node.name}")
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith('_'):
                        exports.append(f"variable:{target.id}")
                        
        return exports
    
    def _extract_public_api(self, files: List[FileContext]) -> List[str]:
        public_api = []

        init_file = None
        for file_ctx in files:
            if file_ctx.path.name == '__init__.py':
                init_file = file_ctx
                break
                
        if init_file and init_file.ast_tree:
            for node in ast.walk(init_file.ast_tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == '__all__':
                            if isinstance(node.value, ast.List):
                                for elt in node.value.elts:
                                    if isinstance(elt, ast.Str):
                                        public_api.append(elt.s)
                                    elif isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                        public_api.append(elt.value)
        
        if not public_api:
            for file_ctx in files:
                public_api.extend(file_ctx.exports)
                
        return public_api
    
    def _analyze_module_dependencies(self, files: List[FileContext]) -> Tuple[Set[str], Set[str]]:
        internal_deps = set()
        external_deps = set()
        
        for file_ctx in files:
            for dep in file_ctx.dependencies:
                dep_path = Path(dep)
                if dep_path.is_relative_to(self.root_path):
                    internal_deps.add(dep)
                else:
                    external_deps.add(dep)
                    
        return internal_deps, external_deps
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        complexity = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With)):
                complexity += 1
            elif isinstance(node, ast.Try):
                complexity += len(node.handlers)
                
        return complexity