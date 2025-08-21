"""Intelligent file patcher for AgentCLI."""

import os
import re
import ast
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class PatchOperation:
    """Represents a specific patch operation."""
    type: str  # 'replace_imports', 'add_import', 'remove_import', 'fix_function', etc.
    line_start: int
    line_end: int
    old_content: str
    new_content: str
    description: str

class IntelligentPatcher:
    """Intelligent file patcher that makes minimal changes."""
    
    def __init__(self):
        pass
    
    def create_import_fix_plan(self, file_path: str, target_imports: List[str]) -> List[PatchOperation]:
        """Create a plan to fix only imports in a file."""
        if not os.path.exists(file_path):
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        operations = []
        
        # Find import section
        import_start, import_end = self._find_import_section(lines)
        
        if import_start >= 0:
            old_imports = '\n'.join(lines[import_start:import_end + 1])
            new_imports = '\n'.join(target_imports)
            
            operations.append(PatchOperation(
                type='replace_imports',
                line_start=import_start,
                line_end=import_end,
                old_content=old_imports,
                new_content=new_imports,
                description=f"Replace imports in lines {import_start+1}-{import_end+1}"
            ))
        
        return operations
    
    def apply_patches(self, file_path: str, operations: List[PatchOperation]) -> str:
        """Apply patch operations to a file and return new content."""
        if not os.path.exists(file_path):
            return ""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Sort operations by line number (reverse to apply from bottom up)
        sorted_ops = sorted(operations, key=lambda x: x.line_start, reverse=True)
        
        for op in sorted_ops:
            if op.type == 'replace_imports':
                # Replace import section
                new_lines = op.new_content.split('\n')
                if new_lines and new_lines[-1] == '':  # Remove empty line at end
                    new_lines = new_lines[:-1]
                
                # Add newline to each line except the last
                new_lines_with_newlines = [line + '\n' for line in new_lines[:-1]]
                if new_lines:  # Add last line
                    new_lines_with_newlines.append(new_lines[-1] + '\n')
                
                lines[op.line_start:op.line_end + 1] = new_lines_with_newlines
        
        return ''.join(lines)
    
    def _find_import_section(self, lines: List[str]) -> Tuple[int, int]:
        """Find the start and end of import section."""
        import_start = -1
        import_end = -1
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip comments and empty lines at the beginning
            if not stripped or stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            
            # Found first import
            if stripped.startswith('import ') or stripped.startswith('from '):
                if import_start == -1:
                    import_start = i
                import_end = i
            
            # Stop at first non-import line (but allow empty lines between imports)
            elif import_start >= 0 and stripped and not (stripped.startswith('import ') or stripped.startswith('from ')):
                break
        
        return import_start, import_end
    
    def extract_current_imports(self, file_path: str) -> List[str]:
        """Extract current import statements from a file."""
        if not os.path.exists(file_path):
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        imports = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                imports.append(stripped)
        
        return imports

# Integration with planning system
class PatchingPlanner:
    """Planner that creates minimal patch-based actions."""
    
    def __init__(self):
        self.patcher = IntelligentPatcher()
    
    def create_import_fix_action(self, file_path: str, project_context: str) -> Dict[str, Any]:
        """Create an action that fixes only imports."""
        
        # Read current file
        if not os.path.exists(file_path):
            return {
                "type": "error",
                "description": f"File {file_path} not found"
            }
        
        with open(file_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        current_imports = self.patcher.extract_current_imports(file_path)
        
        # Create action with current content and specific instructions
        return {
            "type": "patch_imports",
            "path": file_path,
            "description": f"Fix imports in {file_path} while preserving all function implementations",
            "current_content": current_content,
            "current_imports": current_imports,
            "patch_type": "imports_only",
            "instructions": "Only modify import statements. Keep all function bodies and logic exactly as they are."
        }
