"""Data structures for code analysis."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum


class CodeElementType(Enum):
    """Types of code elements."""
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"


@dataclass
class ImportInfo:
    """Information about an import statement."""
    module: str
    names: List[str]  # imported names, empty for star imports
    alias: Optional[str] = None
    is_from_import: bool = False
    line_number: int = 0


@dataclass
class ParameterInfo:
    """Information about function/method parameters."""
    name: str
    type_hint: Optional[str] = None
    default_value: Optional[str] = None
    is_varargs: bool = False
    is_kwargs: bool = False


@dataclass
class FunctionInfo:
    """Information about a function or method."""
    name: str
    line_number: int
    docstring: Optional[str] = None
    parameters: List[ParameterInfo] = None
    return_type: Optional[str] = None
    is_async: bool = False
    is_method: bool = False
    is_property: bool = False
    is_staticmethod: bool = False
    is_classmethod: bool = False
    complexity_score: int = 1

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []


@dataclass  
class ClassInfo:
    """Information about a class."""
    name: str
    line_number: int
    docstring: Optional[str] = None
    base_classes: List[str] = None
    methods: List[FunctionInfo] = None
    properties: List[str] = None
    class_variables: List[str] = None

    def __post_init__(self):
        if self.base_classes is None:
            self.base_classes = []
        if self.methods is None:
            self.methods = []
        if self.properties is None:
            self.properties = []
        if self.class_variables is None:
            self.class_variables = []


@dataclass
class ModuleInfo:
    """Complete information about a Python module."""
    file_path: str
    module_name: str
    docstring: Optional[str] = None
    classes: List[ClassInfo] = None
    functions: List[FunctionInfo] = None
    imports: List[ImportInfo] = None
    constants: List[str] = None
    line_count: int = 0
    complexity_score: int = 0
    
    def __post_init__(self):
        if self.classes is None:
            self.classes = []
        if self.functions is None:
            self.functions = []
        if self.imports is None:
            self.imports = []
        if self.constants is None:
            self.constants = []


@dataclass
class AnalysisResult:
    """Result of module analysis with summary."""
    module_info: ModuleInfo
    summary: str
    key_points: List[str]
    dependencies: List[str]
    complexity_level: str  # "low", "medium", "high"
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []
