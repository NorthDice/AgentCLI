"""
FixManager — intelligent refactoring with logging and rollback support.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import re
from datetime import datetime
from agentcli.core.logger import Logger
from agentcli.utils.logging import logger as app_logger
from agentcli.core.planner import Planner

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

class FixManager:
    def __init__(self, root_path: Path, llm_service, logger=None):
        self.root_path = root_path
        self.llm_service = llm_service
        self.context_builder = ContextBuilder(root_path)
        self.logger = logger or Logger()
        app_logger.info(f"FixManager initialized for {self.root_path}")

    def fix_with_context(self, description: str, target_paths: List[Path], options: Dict[str, Any] = None) -> Dict[str, Any]:
        options = options or {}
        app_logger.info(f"Starting fix_with_context: {description}")
        
        project_context = self.context_builder.build_full_context(target_paths)
        llm_context = self._prepare_llm_context(project_context, target_paths, description)
        
        app_logger.info(f"LLM context prepared, sending to LLM...")
        query = f"{llm_context}\nUser Request: {description}"
        
        planner = Planner()
        raw_plan = planner.create_plan(query) 
        planner.save_plan(raw_plan)

        formatted_plan = {
            'description': description, 
            'changes': [],
            'warnings': [],
            'estimated_impact': 'medium'
        }
        

        if isinstance(raw_plan, dict):
            if 'tasks' in raw_plan:
                formatted_plan['changes'] = [task.get('description', str(task)) for task in raw_plan['tasks']]
            elif 'steps' in raw_plan:
                formatted_plan['changes'] = raw_plan['steps']
            elif 'plan' in raw_plan:
                formatted_plan['changes'] = [raw_plan['plan']] if isinstance(raw_plan['plan'], str) else raw_plan['plan']
            else:
                formatted_plan['changes'] = [str(raw_plan)]
                
            if 'warnings' in raw_plan:
                formatted_plan['warnings'] = raw_plan['warnings']
            if 'risks' in raw_plan:
                formatted_plan['warnings'].extend(raw_plan['risks'])
        else:
            formatted_plan['changes'] = [str(raw_plan)]
        
        validation_result = self._validate_plan(formatted_plan, project_context)
        
        return {
            'plan': formatted_plan,
            'context': project_context,
            'validation': validation_result,
            'target_files': [str(p) for p in target_paths],
            'raw_plan': raw_plan  
        }

    def _prepare_llm_context(self, project_context: ProjectContext, 
                             target_paths: List[Path], description: str) -> str:
        context_parts = []

        context_parts.append(f"""
# PROJECT: {project_context.root_path.name}

## ARCHITECTURE PATTERNS
{chr(10).join(project_context.architecture_patterns) if project_context.architecture_patterns else "No patterns detected"}

## MODULE STRUCTURE
""")

        for name, module in project_context.modules.items():
            context_parts.append(f"""
### Module: {name}
- Path: {module.path}
- Files: {len(module.files)}
- Public API: {', '.join(module.public_api[:10])}{'...' if len(module.public_api) > 10 else ''}
- External dependencies: {len(module.external_dependencies)}
""")

        context_parts.append("\n## TARGET FILES (detailed)\n")

        for target_path in target_paths:
            for module in project_context.modules.values():
                target_file = None
                for file_ctx in module.files:
                    if file_ctx.path == target_path or target_path in [file_ctx.path, file_ctx.path.parent]:
                        target_file = file_ctx
                        break

                if target_file:
                    context_parts.append(f"""
### {target_file.path.name}
```python
# Imports:
{chr(10).join(target_file.imports)}

# Exports: {', '.join(target_file.exports)}
# Dependencies: {len(target_file.dependencies)} files
# Depended on by: {len(target_file.dependents)} files
# Complexity: {target_file.complexity_score}
# Lines of code: {target_file.line_count}

# Content (first 50 lines):
{chr(10).join(target_file.content.splitlines()[:50])}
{'...' if target_file.line_count > 50 else ''}
```
""")


        context_parts.append("\n## DEPENDENCY GRAPH\n")

        for target_path in target_paths:
            target_str = str(target_path)
            if target_str in project_context.dependency_graph:
                deps = project_context.dependency_graph[target_str]
                if deps:
                    context_parts.append(f"**{target_path.name}** depends on:")
                    for dep in list(deps)[:10]:  # Limit number of dependencies shown
                        dep_name = Path(dep).name
                        context_parts.append(f"  - {dep_name}")

            # Find files that depend on this file
            dependents = []
            for file_path, deps in project_context.dependency_graph.items():
                if target_str in deps:
                    dependents.append(Path(file_path).name)

            if dependents:
                context_parts.append(f"**Files depending on {target_path.name}:**")
                for dep in dependents[:10]:  # Limit number of dependents shown
                    context_parts.append(f"  - {dep}")

        # Symbol map
        relevant_symbols = {}
        for target_path in target_paths:
            for symbol, file_path in project_context.global_symbols.items():
                if Path(file_path) == target_path:
                    relevant_symbols[symbol] = file_path

        if relevant_symbols:
            context_parts.append(f"\n## SYMBOLS IN TARGET FILES\n")
            for symbol, file_path in list(relevant_symbols.items())[:20]:
                context_parts.append(f"- **{symbol}** defined in {Path(file_path).name}")

        # Refactoring task
        context_parts.append(f"""
## REFACTORING TASK
{description}

## INSTRUCTIONS
1. Consider all dependencies when making changes
2. Preserve public API of modules
3. Automatically fix imports when moving code
4. Provide a detailed change plan with justification
5. Specify which files will be changed and how
6. Warn about possible issues
""")

        return '\n'.join(context_parts)
    
    def _validate_plan(self, plan: Dict[str, Any], project_context: ProjectContext) -> Dict[str, Any]:
        validation = {
            'is_valid': True,
            'errors': [],
            'suggestions': [],
            'risk_level': 'low'
        }
        
        # Проверяем на наличие циклических зависимостей
        cycles = self.context_builder.dependency_analyzer.find_circular_dependencies(
            project_context.dependency_graph
        )
        
        if cycles:
            validation['errors'].append(f"Обнаружены циклические зависимости: {len(cycles)}")
            validation['risk_level'] = 'high'
            validation['is_valid'] = False
        
        # Проверяем затронутые файлы
        changes = plan.get('changes', [])
        if not changes:
            validation['errors'].append("План не содержит изменений")
            validation['is_valid'] = False
            return validation
            
        affected_files = len([change for change in changes if isinstance(change, str) and 'файл' in change.lower()])
        
        if affected_files > 10:
            validation['suggestions'].append("Много файлов будет изменено. Рассмотрите разбиение на несколько этапов.")
            validation['risk_level'] = 'medium'
        
        # Проверяем на нарушение публичного API
        for module_name, module_ctx in project_context.modules.items():
            if any(isinstance(change, str) and 'удалить' in change.lower() and any(api in change for api in module_ctx.public_api) 
                for change in changes):
                validation['errors'].append(f"Возможное нарушение публичного API модуля {module_name}")
                validation['risk_level'] = 'high'
        
        return validation


    def _apply_single_change(self, change_description: str, project_context: ProjectContext) -> Dict[str, Any]:
        # Only apply 'modify' actions, skip 'info' and others
        if isinstance(change_description, dict):
            action_type = change_description.get('type', '').lower()
            if action_type == 'modify':
                path = change_description.get('path')
                content = change_description.get('content')
                if path and content is not None:
                    try:
                        Path(path).write_text(content, encoding='utf-8')
                        return {'type': 'modify', 'status': 'success', 'path': path}
                    except Exception as e:
                        return {'type': 'modify', 'status': 'error', 'path': path, 'error': str(e)}
                else:
                    return {'type': 'modify', 'status': 'error', 'error': 'Missing path or content'}
            else:
                # Skip 'info' and other actions
                return {'type': action_type, 'status': 'skipped'}
        # Fallback for string-based descriptions
        return {'type': 'unknown', 'description': str(change_description), 'status': 'skipped'}
    
    def _handle_create_file(self, description: str) -> Dict[str, Any]:
        """Handles creation of a new file."""
        # Extract path and content from description
        # This is a simplified example - real parsing will be more complex
        return {'type': 'create', 'status': 'simulated'}
    
    def _handle_modify_file(self, description: str, project_context: ProjectContext) -> Dict[str, Any]:
        """Handles modification of an existing file."""
        return {'type': 'modify', 'status': 'simulated'}
    
    def _handle_move_file(self, description: str, project_context: ProjectContext) -> Dict[str, Any]:
        """Handles moving a file."""
        return {'type': 'move', 'status': 'simulated'}
    
    def _handle_delete_file(self, description: str) -> Dict[str, Any]:
        """Handles file deletion."""
        return {'type': 'delete', 'status': 'simulated'}
    
    def _auto_fix_imports(self, project_context: ProjectContext) -> List[Dict[str, Any]]:
        """Automatically fixes imports after changes."""
        fixes = []
        
        # Проходим по всем файлам и проверяем импорты
        for module_name, module_ctx in project_context.modules.items():
            for file_ctx in module_ctx.files:
                file_fixes = self._fix_file_imports(file_ctx, project_context)
                if file_fixes:
                    fixes.extend(file_fixes)
        
        return fixes
    
    def _fix_file_imports(self, file_ctx: FileContext, project_context: ProjectContext) -> List[Dict[str, Any]]:
        """Fixes imports in a specific file."""
        fixes = []
        
        try:
            lines = file_ctx.content.splitlines()
            modified_lines = []
            
            for line_num, line in enumerate(lines):
                original_line = line
                
                # Проверяем импорты
                if line.strip().startswith(('import ', 'from ')):
                    fixed_line = self._fix_import_line(line, project_context)
                    if fixed_line != line:
                        fixes.append({
                            'file': str(file_ctx.path),
                            'line_number': line_num + 1,
                            'original': original_line,
                            'fixed': fixed_line,
                            'type': 'import_fix'
                        })
                        line = fixed_line
                
                modified_lines.append(line)
            
            # Записываем исправленный файл, если были изменения
            if fixes:
                file_ctx.path.write_text('\n'.join(modified_lines), encoding='utf-8')
                
        except Exception as e:
            fixes.append({
                'file': str(file_ctx.path),
                'error': f"Ошибка при исправлении импортов: {str(e)}",
                'type': 'error'
            })
        
        return fixes
    
    def _fix_import_line(self, import_line: str, project_context: ProjectContext) -> str:
        """Fixes a single import line."""
        # Упрощенная логика исправления импортов
        # В реальности здесь должна быть более сложная логика
        
        # Проверяем, существует ли импортируемый модуль
        if import_line.strip().startswith('from '):
            match = re.match(r'from\s+([^\s]+)\s+import', import_line)
            if match:
                module_name = match.group(1)
                
                # Если модуль не найден в карте импортов, пытаемся найти альтернативу
                if module_name not in project_context.import_map:
                    # Ищем похожие модули
                    similar_modules = [m for m in project_context.import_map.keys() 
                                     if module_name.split('.')[-1] in m]
                    if similar_modules:
                        new_module = similar_modules[0]
                        return import_line.replace(module_name, new_module)
        
        return import_line
    
    def _validate_syntax(self, applied_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validates syntax of changed Python files."""
        syntax_check = {
            'valid_files': [],
            'invalid_files': [],
            'total_checked': 0
        }
        
        # Собираем все измененные Python файлы
        changed_files = set()
        for change in applied_changes:
            if change['status'] == 'success' and 'result' in change:
                result = change['result']
                if 'file_path' in result:
                    file_path = Path(result['file_path'])
                    if file_path.suffix == '.py':
                        changed_files.add(file_path)

        for file_path in changed_files:
            syntax_check['total_checked'] += 1
            
            try:
                content = file_path.read_text(encoding='utf-8')
                ast.parse(content)
                syntax_check['valid_files'].append(str(file_path))
                
            except SyntaxError as e:
                syntax_check['invalid_files'].append({
                    'file': str(file_path),
                    'error': f"Строка {e.lineno}: {e.msg}",
                    'line': e.lineno,
                    'offset': e.offset
                })
            except Exception as e:
                syntax_check['invalid_files'].append({
                    'file': str(file_path),
                    'error': f"Ошибка чтения файла: {str(e)}"
                })
        
        return syntax_check
    
    
    def apply_fix_plan(self, plan_result: Dict[str, Any], confirm_callback=None) -> Dict[str, Any]:
        plan = plan_result['plan']
        project_context = plan_result['context']
        
        if not plan_result['validation']['is_valid']:
            app_logger.error('План не прошел валидацию')
            return {
                'success': False,
                'error': 'План не прошел валидацию',
                'details': plan_result['validation']['errors']
            }
        
        app_logger.info('Применяю план рефакторинга...')
        applied_changes = []
        errors = []
        
        try:
            changes = plan.get('changes', [])
            if not changes:
                return {
                    'success': False,
                    'error': 'План не содержит изменений для применения',
                    'applied_changes': [],
                    'errors': ['Нет изменений в плане']
                }
            
            for i, change_description in enumerate(changes):
                if confirm_callback and not confirm_callback(f"Применить изменение {i+1}: {change_description}?"):
                    continue
                
                try:
                    change_result = self._apply_single_change(str(change_description), project_context)
                    applied_changes.append({
                        'description': str(change_description),
                        'result': change_result,
                        'status': 'success'
                    })
                    
                    # Логируем действие для поддержки rollback
                    if hasattr(self.logger, 'log_action'):
                        self.logger.log_action(change_result.get('type', 'unknown'), str(change_description), change_result)
                        
                except Exception as e:
                    error_msg = f"Ошибка при применении изменения '{change_description}': {str(e)}"
                    errors.append(error_msg)
                    applied_changes.append({
                        'description': str(change_description),
                        'error': error_msg,
                        'status': 'failed'
                    })
                    app_logger.error(error_msg)
            
            # Автоматически исправляем импорты
            import_fixes = self._auto_fix_imports(project_context)
            
            # Проверяем синтаксис измененных файлов
            syntax_check = self._validate_syntax(applied_changes)
            
            return {
                'success': len(errors) == 0,
                'applied_changes': applied_changes,
                'errors': errors,
                'import_fixes': import_fixes,
                'syntax_check': syntax_check
            }
            
        except Exception as e:
            app_logger.error(f"Критическая ошибка при применении плана: {str(e)}")
            return {
                'success': False,
                'error': f"Критическая ошибка при применении плана: {str(e)}",
                'applied_changes': applied_changes,
                'errors': errors
            }
