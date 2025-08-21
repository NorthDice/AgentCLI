"""Structure provider for generating project context."""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict

@dataclass
class FileInfo:
    """Information about a single file."""
    path: str
    type: str  # 'python', 'config', 'test', 'doc', 'other'
    size_lines: int
    imports: List[str] = None
    exports: List[str] = None
    
class StructureProvider:
    """Provides project structure information for LLM context."""
    
    def __init__(self, root_path: str = None):
        """Initialize structure provider.
        
        Args:
            root_path: Root directory of the project. Defaults to current directory.
        """
        self.root_path = root_path or os.getcwd()
        self.ignore_patterns = {
            '__pycache__', '.git', '.pytest_cache', 'node_modules',
            '.venv', 'venv', '.env', 'dist', 'build', '.idea',
            '.vscode', '*.pyc', '*.pyo', '*.egg-info'
        }
        self.max_file_size = 1000  # lines
    
    def get_structure_summary(self, include_content: bool = False) -> str:
        """Get project structure summary for LLM.
        
        Args:
            include_content: Whether to include file contents for small files
            
        Returns:
            Formatted string with project structure
        """
        structure = self._analyze_structure()
        return self._format_for_llm(structure, include_content)
    
    def get_files_context(self, file_patterns: List[str]) -> str:
        """Get context for specific files matching patterns.
        
        Args:
            file_patterns: List of file patterns (names or paths)
            
        Returns:
            Formatted context for matched files
        """
        matched_files = self._find_matching_files(file_patterns)
        context = []
        
        for file_path in matched_files:
            rel_path = os.path.relpath(file_path, self.root_path)
            context.append(f"\n=== File: {rel_path} ===")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    if len(lines) <= 50:  # Small files - full content
                        context.append(content)
                    else:  # Large files - structure only
                        context.append(self._get_file_structure(content, file_path))
                        
            except Exception as e:
                context.append(f"Error reading file: {e}")
        
        return '\n'.join(context)
    
    def _analyze_structure(self) -> Dict:
        """Analyze project structure."""
        structure = {
            'root': self.root_path,
            'directories': [],
            'files': [],
            'python_modules': {},
            'config_files': [],
            'test_files': [],
            'dependencies': {}
        }
        
        for root, dirs, files in os.walk(self.root_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore(d)]
            
            rel_root = os.path.relpath(root, self.root_path)
            if rel_root != '.':
                structure['directories'].append(rel_root)
            
            for file in files:
                if self._should_ignore(file):
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.root_path)
                
                file_info = self._analyze_file(file_path, rel_path)
                structure['files'].append(asdict(file_info))
                
                # Categorize files
                if file_info.type == 'python':
                    structure['python_modules'][rel_path] = {
                        'imports': file_info.imports or [],
                        'exports': file_info.exports or []
                    }
                elif file_info.type == 'config':
                    structure['config_files'].append(rel_path)
                elif file_info.type == 'test':
                    structure['test_files'].append(rel_path)
        
        return structure
    
    def _analyze_file(self, file_path: str, rel_path: str) -> FileInfo:
        """Analyze a single file."""
        file_type = self._determine_file_type(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                size_lines = len(lines)
                
                imports, exports = None, None
                if file_type == 'python' and size_lines <= self.max_file_size:
                    imports, exports = self._extract_python_info(content)
                
                return FileInfo(
                    path=rel_path,
                    type=file_type,
                    size_lines=size_lines,
                    imports=imports,
                    exports=exports
                )
        except Exception:
            return FileInfo(
                path=rel_path,
                type=file_type,
                size_lines=0
            )
    
    def _determine_file_type(self, file_path: str) -> str:
        """Determine file type based on extension and path."""
        ext = os.path.splitext(file_path)[1].lower()
        name = os.path.basename(file_path).lower()
        
        if ext == '.py':
            if 'test' in name or '/test' in file_path.lower():
                return 'test'
            return 'python'
        elif ext in ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg']:
            return 'config'
        elif ext in ['.md', '.txt', '.rst']:
            return 'doc'
        else:
            return 'other'
    
    def _extract_python_info(self, content: str) -> tuple:
        """Extract imports and exports from Python file."""
        imports = []
        exports = []
        
        lines = content.split('\n')
        for line in lines:
            stripped = line.strip()
            
            # Extract imports
            if stripped.startswith('import ') or stripped.startswith('from '):
                imports.append(stripped)
            
            # Extract function/class definitions (exports)
            if stripped.startswith('def ') or stripped.startswith('class '):
                name = stripped.split('(')[0].split(':')[0]
                if 'def ' in name:
                    name = name.replace('def ', '').strip()
                elif 'class ' in name:
                    name = name.replace('class ', '').strip()
                
                if not name.startswith('_'):  # Skip private
                    exports.append(name)
        
        return imports[:10], exports[:20]  # Limit to avoid too much data
    
    def _format_for_llm(self, structure: Dict, include_content: bool = False) -> str:
        """Format structure for LLM consumption."""
        lines = []
        
        lines.append("=== PROJECT STRUCTURE ===")
        lines.append(f"Root: {structure['root']}")
        lines.append("")
        
        # Directory structure
        lines.append("📁 DIRECTORIES:")
        for dir_path in sorted(structure['directories'])[:20]:  # Limit output
            lines.append(f"  {dir_path}/")
        lines.append("")
        
        # Python modules
        if structure['python_modules']:
            lines.append("🐍 PYTHON MODULES:")
            
            # Prioritize modules by importance
            modules = list(structure['python_modules'].items())
            prioritized = []
            regular = []
            
            for module, info in modules:
                # Prioritize main app modules, models, and mentioned files
                if (module.startswith('app/') or 
                    module.startswith('models/') or 
                    'main.py' in module or
                    'crud.py' in module):
                    prioritized.append((module, info))
                else:
                    regular.append((module, info))
            
            # Show prioritized first, then regular modules (limit total to 20)
            all_modules = prioritized + regular
            for module, info in all_modules[:20]:
                lines.append(f"  {module}")
                if info['exports']:
                    lines.append(f"    Exports: {', '.join(info['exports'][:5])}")
                if info['imports'] and len(info['imports']) <= 3:
                    lines.append(f"    Imports: {', '.join(info['imports'])}")
            lines.append("")
        
        # Config files
        if structure['config_files']:
            lines.append("⚙️ CONFIG FILES:")
            for config in structure['config_files'][:10]:
                lines.append(f"  {config}")
            lines.append("")
        
        # Test files
        if structure['test_files']:
            lines.append("🧪 TEST FILES:")
            for test in structure['test_files'][:10]:
                lines.append(f"  {test}")
            lines.append("")
        
        # File summary
        total_files = len(structure['files'])
        python_files = len(structure['python_modules'])
        lines.append(f"📊 SUMMARY: {total_files} files total, {python_files} Python modules")
        
        return '\n'.join(lines)
    
    def _find_matching_files(self, patterns: List[str]) -> List[str]:
        """Find files matching given patterns."""
        matched = []
        
        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if not self._should_ignore(d)]
            
            for file in files:
                if self._should_ignore(file):
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.root_path)
                
                # Check if file matches any pattern
                for pattern in patterns:
                    if (pattern in file or 
                        pattern in rel_path or 
                        os.path.basename(file_path) == pattern):
                        matched.append(file_path)
                        break
        
        return matched
    
    def _get_file_structure(self, content: str, file_path: str) -> str:
        """Get structure overview of a large file."""
        if not file_path.endswith('.py'):
            return f"Large file ({len(content.split())} lines) - content truncated"
        
        lines = content.split('\n')
        structure_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (stripped.startswith('class ') or 
                stripped.startswith('def ') or
                stripped.startswith('import ') or
                stripped.startswith('from ')):
                structure_lines.append(f"{i+1:4d}: {line}")
        
        return '\n'.join(structure_lines[:30])  # Limit structure lines
    
    def _should_ignore(self, name: str) -> bool:
        """Check if file/directory should be ignored."""
        for pattern in self.ignore_patterns:
            if pattern.startswith('*'):
                if name.endswith(pattern[1:]):
                    return True
            elif pattern in name:
                return True
        return False
