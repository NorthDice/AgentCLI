"""Module analyzer using AST for Python code analysis."""

import ast
import os
from pathlib import Path
from typing import List, Optional, Set, Union

from .models import (
    ModuleInfo, ClassInfo, FunctionInfo, ImportInfo, 
    ParameterInfo, CodeElementType
)


class ModuleAnalyzer:
    """Analyzer for Python modules using AST."""
    
    def __init__(self):
        self.supported_extensions = {'.py'}
    
    def analyze_file(self, file_path: str) -> Optional[ModuleInfo]:
        """Analyze a Python file and extract structure information.
        
        Args:
            file_path (str): Path to the Python file
            
        Returns:
            Optional[ModuleInfo]: Module information or None if analysis failed
        """
        if not self._is_python_file(file_path):
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content, filename=file_path)
            return self._extract_module_info(tree, file_path, content)
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def _is_python_file(self, file_path: str) -> bool:
        """Check if file is a Python file."""
        return Path(file_path).suffix in self.supported_extensions
    
    def _extract_module_info(self, tree: ast.AST, file_path: str, content: str) -> ModuleInfo:
        """Extract module information from AST."""
        module_name = Path(file_path).stem
        
        # Extract module docstring
        docstring = ast.get_docstring(tree)
        
        # Initialize lists
        classes = []
        functions = []
        imports = []
        constants = []
        
        # Walk through AST nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info(node)
                classes.append(class_info)
                
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Only top-level functions (not methods)
                if self._is_top_level_function(node, tree):
                    func_info = self._extract_function_info(node)
                    functions.append(func_info)
                    
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_info = self._extract_import_info(node)
                imports.append(import_info)
                
            elif isinstance(node, ast.Assign):
                # Extract module-level constants
                constants.extend(self._extract_constants(node))
        
        # Calculate metrics
        line_count = len(content.splitlines())
        complexity_score = self._calculate_complexity(tree)
        
        return ModuleInfo(
            file_path=file_path,
            module_name=module_name,
            docstring=docstring,
            classes=classes,
            functions=functions,
            imports=imports,
            constants=constants,
            line_count=line_count,
            complexity_score=complexity_score
        )
    
    def _extract_class_info(self, node: ast.ClassDef) -> ClassInfo:
        """Extract information about a class."""
        docstring = ast.get_docstring(node)
        
        # Extract base classes
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(self._get_attribute_name(base))
        
        # Extract methods
        methods = []
        properties = []
        class_variables = []
        
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = self._extract_function_info(item, is_method=True)
                
                # Check for properties
                if self._is_property(item):
                    properties.append(func_info.name)
                    func_info.is_property = True
                
                methods.append(func_info)
                
            elif isinstance(item, ast.Assign):
                # Class variables
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        class_variables.append(target.id)
        
        return ClassInfo(
            name=node.name,
            line_number=node.lineno,
            docstring=docstring,
            base_classes=base_classes,
            methods=methods,
            properties=properties,
            class_variables=class_variables
        )
    
    def _extract_function_info(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], 
                              is_method: bool = False) -> FunctionInfo:
        """Extract information about a function or method."""
        docstring = ast.get_docstring(node)
        
        # Extract parameters
        parameters = []
        args = node.args
        
        # Regular arguments
        for i, arg in enumerate(args.args):
            param_info = ParameterInfo(
                name=arg.arg,
                type_hint=self._get_type_annotation(arg),
            )
            
            # Check for default values
            defaults_offset = len(args.args) - len(args.defaults)
            if i >= defaults_offset:
                default_index = i - defaults_offset
                param_info.default_value = self._get_default_value(args.defaults[default_index])
            
            parameters.append(param_info)
        
        # *args
        if args.vararg:
            parameters.append(ParameterInfo(
                name=args.vararg.arg,
                type_hint=self._get_type_annotation(args.vararg),
                is_varargs=True
            ))
        
        # **kwargs  
        if args.kwarg:
            parameters.append(ParameterInfo(
                name=args.kwarg.arg,
                type_hint=self._get_type_annotation(args.kwarg),
                is_kwargs=True
            ))
        
        # Return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
        
        # Check decorators
        is_staticmethod = any(self._is_decorator(d, 'staticmethod') for d in node.decorator_list)
        is_classmethod = any(self._is_decorator(d, 'classmethod') for d in node.decorator_list)
        is_property = any(self._is_decorator(d, 'property') for d in node.decorator_list)
        
        # Calculate complexity
        complexity = self._calculate_function_complexity(node)
        
        return FunctionInfo(
            name=node.name,
            line_number=node.lineno,
            docstring=docstring,
            parameters=parameters,
            return_type=return_type,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=is_method,
            is_property=is_property,
            is_staticmethod=is_staticmethod,
            is_classmethod=is_classmethod,
            complexity_score=complexity
        )
    
    def _extract_import_info(self, node: Union[ast.Import, ast.ImportFrom]) -> ImportInfo:
        """Extract import information."""
        if isinstance(node, ast.Import):
            # import module [as alias]
            for alias in node.names:
                return ImportInfo(
                    module=alias.name,
                    names=[],
                    alias=alias.asname,
                    is_from_import=False,
                    line_number=node.lineno
                )
        else:
            # from module import name [as alias]
            names = []
            for alias in node.names:
                if alias.name == '*':
                    names = ['*']
                else:
                    names.append(alias.name)
            
            return ImportInfo(
                module=node.module or '',
                names=names,
                is_from_import=True,
                line_number=node.lineno
            )
    
    def _extract_constants(self, node: ast.Assign) -> List[str]:
        """Extract module-level constants."""
        constants = []
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id.isupper():
                constants.append(target.id)
        return constants
    
    def _is_top_level_function(self, func_node: ast.FunctionDef, tree: ast.AST) -> bool:
        """Check if function is defined at module level."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if item is func_node:
                        return False
        return True
    
    def _is_property(self, node: ast.FunctionDef) -> bool:
        """Check if function is a property."""
        return any(self._is_decorator(d, 'property') for d in node.decorator_list)
    
    def _is_decorator(self, decorator: ast.expr, name: str) -> bool:
        """Check if decorator matches given name."""
        if isinstance(decorator, ast.Name):
            return decorator.id == name
        elif isinstance(decorator, ast.Attribute):
            return decorator.attr == name
        return False
    
    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Get full attribute name."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        return node.attr
    
    def _get_type_annotation(self, arg: ast.arg) -> Optional[str]:
        """Get type annotation as string."""
        if arg.annotation:
            try:
                if hasattr(ast, 'unparse'):
                    return ast.unparse(arg.annotation)
                else:
                    return str(arg.annotation)
            except:
                return None
        return None
    
    def _get_default_value(self, node: ast.expr) -> str:
        """Get default value as string."""
        try:
            if hasattr(ast, 'unparse'):
                return ast.unparse(node)
            elif isinstance(node, ast.Constant):
                return repr(node.value)
            elif isinstance(node, ast.NameConstant):
                return str(node.value)
            else:
                return "..."
        except:
            return "..."
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate overall module complexity."""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, (ast.Try, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                complexity += 1
        
        return complexity
    
    def _calculate_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1 
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.Try, ast.ExceptHandler)):
                complexity += 1
        
        return complexity
