import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict, deque

from .models import FileContext, ModuleContext, ProjectContext
from .dependency_analyzer import DependencyAnalyzer
from .structure_analyzer import ModuleStructureAnalyzer

class ContextBuilder:
    """Builds full project context for LLM."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.dependency_analyzer = DependencyAnalyzer(root_path)
        self.module_analyzer = ModuleStructureAnalyzer(root_path)
        
    def build_full_context(self, target_files: List[Path]) -> ProjectContext:
        # 1. Находим все релевантные файлы
        relevant_files = self._find_relevant_files(target_files)
        
        # 2. Анализируем каждый файл
        file_contexts = []
        for file_path in relevant_files:
            file_ctx = self.module_analyzer._analyze_single_file(file_path)
            if file_ctx:
                file_contexts.append(file_ctx)
        
        # 3. Строим граф зависимостей
        dependency_graph = self.dependency_analyzer.build_dependency_graph(file_contexts)
        
        # 4. Заполняем dependents
        for file_ctx in file_contexts:
            file_path = str(file_ctx.path)
            for other_file, deps in dependency_graph.items():
                if file_path in deps:
                    file_ctx.dependents.add(other_file)
        
        # 5. Группируем по модулям
        modules = self._group_files_by_modules(file_contexts)
        
        # 6. Строим карты импортов и символов
        import_map, global_symbols = self._build_symbol_maps(file_contexts)
        
        # 7. Выявляем архитектурные паттерны
        patterns = self._detect_architecture_patterns(modules, dependency_graph)
        
        # 8. Находим конфигурационные и тестовые файлы
        config_files = self._find_config_files()
        test_files = self._find_test_files()
        
        return ProjectContext(
            root_path=self.root_path,
            modules=modules,
            dependency_graph=dependency_graph,
            import_map=import_map,
            global_symbols=global_symbols,
            architecture_patterns=patterns,
            config_files=config_files,
            test_files=test_files
        )
    
    def _find_relevant_files(self, target_files: List[Path], max_depth: int = 3) -> Set[Path]:
        relevant = set()
        queue = deque([(f, 0) for f in target_files])
        visited = set()
        
        while queue:
            current_file, depth = queue.popleft()
            
            if current_file in visited or depth > max_depth:
                continue
                
            visited.add(current_file)
            relevant.add(current_file)
            
            # Находим зависимости и зависимых
            if current_file.exists() and current_file.suffix == '.py':
                try:
                    content = current_file.read_text(encoding='utf-8')
                    _, dependencies = self.dependency_analyzer.analyze_file_imports(current_file, content)
                    
                    for dep_path_str in dependencies:
                        dep_path = Path(dep_path_str)
                        if dep_path not in visited:
                            queue.append((dep_path, depth + 1))
                            
                except (UnicodeDecodeError, PermissionError):
                    continue
        
        return relevant
    
    def _group_files_by_modules(self, file_contexts: List[FileContext]) -> Dict[str, ModuleContext]:
        modules = {}
        
        # Группируем по директориям
        dirs_to_files = defaultdict(list)
        for file_ctx in file_contexts:
            parent_dir = file_ctx.path.parent
            dirs_to_files[parent_dir].append(file_ctx)
        
        # Создаем контексты модулей
        for dir_path, files in dirs_to_files.items():
            module_name = dir_path.name
            if dir_path == self.root_path:
                module_name = "root"
                
            # Анализируем зависимости модуля
            internal_deps = set()
            external_deps = set()
            
            for file_ctx in files:
                for dep in file_ctx.dependencies:
                    dep_path = Path(dep)
                    if dep_path.is_relative_to(self.root_path):
                        if dep_path.parent != dir_path:
                            internal_deps.add(dep)
                    else:
                        external_deps.add(dep)
            
            # Публичное API
            public_api = []
            for file_ctx in files:
                if file_ctx.path.name == '__init__.py':
                    public_api.extend(file_ctx.exports)
                    break
            else:
                # Если нет __init__.py, берем все публичные символы
                for file_ctx in files:
                    public_api.extend([exp for exp in file_ctx.exports if not exp.split(':')[1].startswith('_')])
            
            modules[module_name] = ModuleContext(
                name=module_name,
                path=dir_path,
                files=files,
                submodules=[],  # Упрощено для примера
                public_api=public_api,
                internal_dependencies=internal_deps,
                external_dependencies=external_deps
            )
        
        return modules
    
    def _build_symbol_maps(self, file_contexts: List[FileContext]) -> Tuple[Dict[str, str], Dict[str, str]]:
        import_map = {}
        global_symbols = {}
        
        for file_ctx in file_contexts:
            file_path = str(file_ctx.path)
            
            # Регистрируем все экспорты как глобальные символы
            for export in file_ctx.exports:
                symbol_type, symbol_name = export.split(':', 1)
                global_symbols[symbol_name] = file_path
                
            # Строим карту импортов (модуль -> файл)
            for imp in file_ctx.imports:
                if imp.startswith('from '):
                    match = re.match(r'from\s+([^\s]+)\s+import', imp)
                    if match:
                        module_name = match.group(1)
                        import_map[module_name] = file_path
                elif imp.startswith('import '):
                    module_name = imp.split()[1].split('.')[0]
                    import_map[module_name] = file_path
        
        return import_map, global_symbols
    
    def _detect_architecture_patterns(self, modules: Dict[str, ModuleContext], 
                                    dependency_graph: Dict[str, Set[str]]) -> List[str]:
        patterns = []
        
        module_names = set(modules.keys())
        
        if 'models' in module_names and 'views' in module_names:
            patterns.append('MVC-like structure')
            
        if 'services' in module_names or 'handlers' in module_names:
            patterns.append('Service layer pattern')
            
        if 'utils' in module_names or 'helpers' in module_names:
            patterns.append('Utility modules')
            
        if 'config' in module_names or 'settings' in module_names:
            patterns.append('Configuration management')
        
        cycles = self.dependency_analyzer.find_circular_dependencies(dependency_graph)
        if cycles:
            patterns.append(f'Circular dependencies detected: {len(cycles)} cycles')
        
        return patterns
    
    def _find_config_files(self) -> List[Path]:
        config_patterns = [
            '**/*.json', '**/*.yaml', '**/*.yml', '**/*.toml', '**/*.ini',
            '**/config.py', '**/settings.py', '**/.env*', '**/requirements*.txt'
        ]
        
        config_files = []
        for pattern in config_patterns:
            config_files.extend(self.root_path.glob(pattern))
            
        return config_files[:20]  
    
    def _find_test_files(self) -> List[Path]:
        test_patterns = [
            '**/test_*.py', '**/*_test.py', '**/tests/**/*.py'
        ]
        
        test_files = []
        for pattern in test_patterns:
            test_files.extend(self.root_path.glob(pattern))
            
        return test_files[:30]