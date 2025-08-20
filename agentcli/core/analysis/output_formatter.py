"""Output formatter for code analysis results."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich.syntax import Syntax
from rich.columns import Columns
from rich.markdown import Markdown

from .models import AnalysisResult, ModuleInfo, ClassInfo, FunctionInfo


class OutputFormatter:
    """Formats analysis results for beautiful console output."""
    
    def __init__(self):
        self.console = Console()
    
    def format_analysis(self, result: AnalysisResult, verbose: bool = False) -> None:
        """Format and display complete analysis results.
        
        Args:
            result (AnalysisResult): Analysis results to format
            verbose (bool): Whether to show detailed information
        """
        self._print_header(result.module_info)
        self._print_summary(result)
        
        if verbose:
            self._print_detailed_structure(result.module_info)
        else:
            self._print_basic_structure(result.module_info)
        
        self._print_dependencies(result)
        self._print_recommendations(result)
    
    def _print_header(self, module_info: ModuleInfo) -> None:
        """Print module header information."""
        # Create title
        title = f"📄 Module Analysis: {module_info.module_name}"
        
        # Create subtitle with metrics
        metrics = []
        metrics.append(f"📊 {module_info.line_count} lines")
        metrics.append(f"🔧 {len(module_info.functions)} functions")
        metrics.append(f"🏗️ {len(module_info.classes)} classes")
        
        subtitle = " • ".join(metrics)
        
        # Create header panel
        header_content = f"[bold]{title}[/bold]\\n{subtitle}\\n[dim]{module_info.file_path}[/dim]"
        
        panel = Panel(
            header_content,
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print()
    
    def _print_summary(self, result: AnalysisResult) -> None:
        """Print module summary and key points."""
        # Summary section
        summary_panel = Panel(
            result.summary,
            title="📋 Summary",
            border_style="green",
            padding=(1, 2)
        )
        self.console.print(summary_panel)
        
        # Key points
        if result.key_points:
            self.console.print("\\n[bold]🔑 Key Points:[/bold]")
            for i, point in enumerate(result.key_points, 1):
                self.console.print(f"  {i}. {point}")
        
        # Complexity indicator
        complexity_color = {
            "low": "green",
            "medium": "yellow", 
            "high": "red"
        }.get(result.complexity_level, "white")
        
        complexity_text = Text(f"Complexity: {result.complexity_level.upper()}", style=complexity_color)
        self.console.print(f"\\n🎯 ", end="")
        self.console.print(complexity_text)
        self.console.print()
    
    def _print_basic_structure(self, module_info: ModuleInfo) -> None:
        """Print basic module structure overview."""
        if not module_info.classes and not module_info.functions:
            self.console.print("[dim]No classes or functions found[/dim]\\n")
            return
        
        # Create structure tree
        tree = Tree("📁 Module Structure", style="bold blue")
        
        # Add classes
        if module_info.classes:
            classes_branch = tree.add("🏗️ Classes", style="bold green")
            for cls in module_info.classes:
                class_text = f"{cls.name}"
                if cls.base_classes:
                    class_text += f" extends {', '.join(cls.base_classes)}"
                
                class_branch = classes_branch.add(class_text)
                if cls.methods:
                    methods_summary = f"{len(cls.methods)} methods"
                    if cls.properties:
                        methods_summary += f", {len(cls.properties)} properties"
                    class_branch.add(f"📋 {methods_summary}", style="dim")
        
        # Add functions
        if module_info.functions:
            functions_branch = tree.add("🔧 Functions", style="bold yellow")
            for func in module_info.functions:
                func_text = func.name
                if func.is_async:
                    func_text = f"async {func_text}"
                
                func_info = f"{func_text}({len(func.parameters)} params)"
                if func.complexity_score > 5:
                    func_info += " ⚠️"
                
                functions_branch.add(func_info)
        
        self.console.print(tree)
        self.console.print()
    
    def _print_detailed_structure(self, module_info: ModuleInfo) -> None:
        """Print detailed module structure with full information."""
        # Classes details
        if module_info.classes:
            self.console.print("[bold]🏗️ Classes Detail:[/bold]")
            for cls in module_info.classes:
                self._print_class_details(cls)
        
        # Functions details
        if module_info.functions:
            self.console.print("[bold]🔧 Functions Detail:[/bold]")
            for func in module_info.functions:
                self._print_function_details(func)
        
        # Constants
        if module_info.constants:
            self.console.print("[bold]📊 Constants:[/bold]")
            self.console.print(f"  {', '.join(module_info.constants)}")
            self.console.print()
    
    def _print_class_details(self, class_info: ClassInfo) -> None:
        """Print detailed information about a class."""
        # Class header
        class_name = class_info.name
        if class_info.base_classes:
            class_name += f"({', '.join(class_info.base_classes)})"
        
        class_table = Table(title=f"Class: {class_name}", show_header=True, header_style="bold magenta")
        class_table.add_column("Type", style="cyan", width=12)
        class_table.add_column("Name", style="white")
        class_table.add_column("Details", style="dim")
        
        # Add methods
        for method in class_info.methods:
            method_type = "🏷️ Property" if method.is_property else "🔧 Method"
            if method.is_staticmethod:
                method_type = "🔧 Static"
            elif method.is_classmethod:
                method_type = "🔧 Class"
            
            details = f"{len(method.parameters)} params"
            if method.complexity_score > 5:
                details += f", complexity: {method.complexity_score}"
            
            class_table.add_row(method_type, method.name, details)
        
        # Add properties as separate entries
        for prop in class_info.properties:
            class_table.add_row("🏷️ Property", prop, "")
        
        # Add class variables
        for var in class_info.class_variables:
            class_table.add_row("📊 Variable", var, "")
        
        self.console.print(class_table)
        
        # Class docstring
        if class_info.docstring:
            doc_panel = Panel(
                class_info.docstring,
                title="Documentation",
                border_style="dim",
                padding=(0, 1)
            )
            self.console.print(doc_panel)
        
        self.console.print()
    
    def _print_function_details(self, func_info: FunctionInfo) -> None:
        """Print detailed information about a function."""
        # Function signature
        params = []
        for param in func_info.parameters:
            param_str = param.name
            if param.type_hint:
                param_str += f": {param.type_hint}"
            if param.default_value:
                param_str += f" = {param.default_value}"
            if param.is_varargs:
                param_str = f"*{param_str}"
            elif param.is_kwargs:
                param_str = f"**{param_str}"
            params.append(param_str)
        
        signature = f"{func_info.name}({', '.join(params)})"
        if func_info.return_type:
            signature += f" -> {func_info.return_type}"
        
        # Function info table
        func_table = Table(show_header=False, box=None, padding=(0, 1))
        func_table.add_column("", style="cyan", width=12)
        func_table.add_column("", style="white")
        
        func_table.add_row("🔧 Function:", signature)
        func_table.add_row("📍 Line:", str(func_info.line_number))
        func_table.add_row("🎯 Complexity:", str(func_info.complexity_score))
        
        if func_info.is_async:
            func_table.add_row("⚡ Type:", "Async function")
        
        self.console.print(func_table)
        
        # Function docstring
        if func_info.docstring:
            doc_panel = Panel(
                func_info.docstring,
                border_style="dim",
                padding=(0, 1)
            )
            self.console.print(doc_panel)
        
        self.console.print()
    
    def _print_dependencies(self, result: AnalysisResult) -> None:
        """Print dependency information."""
        if not result.dependencies:
            return
        
        self.console.print("[bold]🔗 Dependencies:[/bold]")
        for dep in result.dependencies:
            self.console.print(f"  • {dep}")
        self.console.print()
    
    def _print_recommendations(self, result: AnalysisResult) -> None:
        """Print recommendations for improvement."""
        if not result.recommendations:
            return
        
        recommendations_text = "\\n".join(f"• {rec}" for rec in result.recommendations)
        
        rec_panel = Panel(
            recommendations_text,
            title="💡 Recommendations",
            border_style="yellow",
            padding=(1, 2)
        )
        
        self.console.print(rec_panel)
