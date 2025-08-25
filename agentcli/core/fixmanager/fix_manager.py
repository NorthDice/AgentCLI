import ast
import re
from pathlib import Path
from typing import Dict, List, Any

from agentcli.core.logger import Logger
from agentcli.utils.logging import logger as app_logger
from agentcli.core.planner import Planner

from .models import ProjectContext
from .context_builder import ContextBuilder

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
    
    def _fix_file_imports(self, file_ctx, project_context: ProjectContext) -> List[Dict[str, Any]]:
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