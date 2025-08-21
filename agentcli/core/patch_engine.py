"""Universal patch engine for precise code modifications."""

import re
import ast
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class PatchAction:
    """Represents a single patch action."""
    type: str  # 'replace', 'insert_before', 'insert_after', 'delete'
    target: str  # what to find (line, function, import, etc.)
    content: str = None  # new content
    line_number: int = None  # specific line if applicable
    
class PatchEngine:
    """Engine for applying precise patches to code files."""
    
    def __init__(self):
        self.supported_types = {
            'replace_imports',      # Replace import section
            'replace_function',     # Replace specific function
            'replace_class',        # Replace specific class
            'replace_line',         # Replace specific line(s)
            'insert_before',        # Insert before target
            'insert_after',         # Insert after target
            'delete_lines',         # Delete specific lines
            'replace_block',        # Replace code block between markers
        }
    
    def apply_patches(self, file_path: str, patches: List[Dict[str, Any]]) -> bool:
        """Apply multiple patches to a file.
        
        Args:
            file_path: Path to the file to patch
            patches: List of patch definitions
            
        Returns:
            bool: True if all patches applied successfully
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read original content
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        modified_content = original_content
        
        # Apply patches in order
        for patch_def in patches:
            patch_type = patch_def.get('type')
            if patch_type not in self.supported_types:
                raise ValueError(f"Unsupported patch type: {patch_type}")
            
            modified_content = self._apply_single_patch(
                modified_content, 
                patch_def, 
                file_path
            )
        
        # Write modified content back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        return True
    
    def _apply_single_patch(self, content: str, patch_def: Dict[str, Any], file_path: str) -> str:
        """Apply a single patch to content."""
        patch_type = patch_def['type']
        
        if patch_type == 'replace_imports':
            return self._replace_imports(content, patch_def)
        elif patch_type == 'replace_function':
            return self._replace_function(content, patch_def)
        elif patch_type == 'replace_class':
            return self._replace_class(content, patch_def)
        elif patch_type == 'replace_line':
            return self._replace_line(content, patch_def)
        elif patch_type == 'insert_before':
            return self._insert_before(content, patch_def)
        elif patch_type == 'insert_after':
            return self._insert_after(content, patch_def)
        elif patch_type == 'delete_lines':
            return self._delete_lines(content, patch_def)
        elif patch_type == 'replace_block':
            return self._replace_block(content, patch_def)
        else:
            raise ValueError(f"Unknown patch type: {patch_type}")
    
    def _replace_imports(self, content: str, patch_def: Dict[str, Any]) -> str:
        """Replace import section at the top of the file."""
        lines = content.split('\n')
        new_imports = patch_def['content'].strip().split('\n')
        
        # Find import section boundaries
        first_import = None
        last_import = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                if first_import is None:
                    first_import = i
                last_import = i
        
        if first_import is not None:
            # Replace existing imports
            new_lines = (
                lines[:first_import] + 
                new_imports + 
                lines[last_import + 1:]
            )
        else:
            # No existing imports, add at the top (after docstring/comments)
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""') and not line.strip().startswith("'''"):
                    insert_pos = i
                    break
            
            new_lines = lines[:insert_pos] + new_imports + [''] + lines[insert_pos:]
        
        return '\n'.join(new_lines)
    
    def _replace_function(self, content: str, patch_def: Dict[str, Any]) -> str:
        """Replace a specific function."""
        function_name = patch_def['target']
        new_function = patch_def['content']
        
        if not content.endswith('.py'):
            # For non-Python files, use regex
            return self._replace_with_regex(content, patch_def)
        
        try:
            tree = ast.parse(content)
            lines = content.split('\n')
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    start_line = node.lineno - 1
                    end_line = node.end_lineno
                    
                    # Replace function
                    new_lines = (
                        lines[:start_line] + 
                        new_function.split('\n') + 
                        lines[end_line:]
                    )
                    return '\n'.join(new_lines)
            
        except SyntaxError:
            # If AST parsing fails, fall back to regex
            pass
        
        return self._replace_with_regex(content, patch_def)
    
    def _replace_class(self, content: str, patch_def: Dict[str, Any]) -> str:
        """Replace a specific class."""
        # Get class name from 'target', 'class_name' field or extract from content
        class_name = patch_def.get('target') or patch_def.get('class_name')
        if not class_name:
            # Try to extract class name from the new content
            new_content = patch_def['content']
            try:
                tree = ast.parse(new_content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name
                        break
            except SyntaxError:
                # Fall back to regex if AST fails
                import re
                match = re.search(r'class\s+(\w+)', new_content)
                if match:
                    class_name = match.group(1)
        
        if not class_name:
            raise ValueError("Could not determine class name for replacement")
        
        new_class = patch_def['content']
        
        try:
            tree = ast.parse(content)
            lines = content.split('\n')
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    start_line = node.lineno - 1
                    end_line = node.end_lineno
                    
                    # Replace class
                    new_lines = (
                        lines[:start_line] + 
                        new_class.split('\n') + 
                        lines[end_line:]
                    )
                    return '\n'.join(new_lines)
            
        except SyntaxError:
            pass
        
        return self._replace_with_regex(content, patch_def)
    
    def _replace_line(self, content: str, patch_def: Dict[str, Any]) -> str:
        """Replace specific line(s)."""
        lines = content.split('\n')
        
        if 'line_number' in patch_def:
            # Replace by line number
            line_num = patch_def['line_number'] - 1  # Convert to 0-based
            if 0 <= line_num < len(lines):
                lines[line_num] = patch_def['content']
        else:
            # Replace by content match
            target = patch_def['target']
            new_content = patch_def['content']
            
            for i, line in enumerate(lines):
                if target in line:
                    lines[i] = new_content
                    break
        
        return '\n'.join(lines)
    
    def _insert_before(self, content: str, patch_def: Dict[str, Any]) -> str:
        """Insert content before target."""
        lines = content.split('\n')
        target = patch_def['target']
        new_content = patch_def['content']
        
        for i, line in enumerate(lines):
            if target in line:
                lines.insert(i, new_content)
                break
        
        return '\n'.join(lines)
    
    def _insert_after(self, content: str, patch_def: Dict[str, Any]) -> str:
        """Insert content after target."""
        lines = content.split('\n')
        target = patch_def['target']
        new_content = patch_def['content']
        
        for i, line in enumerate(lines):
            if target in line:
                lines.insert(i + 1, new_content)
                break
        
        return '\n'.join(lines)
    
    def _delete_lines(self, content: str, patch_def: Dict[str, Any]) -> str:
        """Delete specific lines."""
        lines = content.split('\n')
        
        if 'line_numbers' in patch_def:
            # Delete by line numbers
            line_numbers = sorted(patch_def['line_numbers'], reverse=True)
            for line_num in line_numbers:
                if 0 <= line_num - 1 < len(lines):
                    del lines[line_num - 1]
        else:
            # Delete by content match
            target = patch_def['target']
            lines = [line for line in lines if target not in line]
        
        return '\n'.join(lines)
    
    def _replace_block(self, content: str, patch_def: Dict[str, Any]) -> str:
        """Replace a block of code between markers."""
        start_marker = patch_def.get('start_marker')
        end_marker = patch_def.get('end_marker')
        new_content = patch_def['content']
        
        if not start_marker or not end_marker:
            raise ValueError("Block replacement requires start_marker and end_marker")
        
        lines = content.split('\n')
        start_idx = None
        end_idx = None
        
        for i, line in enumerate(lines):
            if start_marker in line and start_idx is None:
                start_idx = i
            if end_marker in line and start_idx is not None:
                end_idx = i
                break
        
        if start_idx is not None and end_idx is not None:
            new_lines = (
                lines[:start_idx + 1] + 
                new_content.split('\n') + 
                lines[end_idx:]
            )
            return '\n'.join(new_lines)
        
        return content
    
    def _replace_with_regex(self, content: str, patch_def: Dict[str, Any]) -> str:
        """Fallback: replace using regex patterns."""
        target = patch_def['target']
        new_content = patch_def['content']
        
        # Try to find and replace the target pattern
        pattern = re.escape(target)
        return re.sub(pattern, new_content, content, count=1)
    
    def preview_patches(self, file_path: str, patches: List[Dict[str, Any]]) -> str:
        """Preview what the file would look like after applying patches."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for patch_def in patches:
            content = self._apply_single_patch(content, patch_def, file_path)
        
        return content
