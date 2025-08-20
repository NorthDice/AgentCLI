"""Команда explain для объяснения кода."""

import click
import os
from rich.console import Console

from agentcli.core.analysis.module_analyzer import ModuleAnalyzer
from agentcli.core.analysis.code_summarizer import CodeSummarizer
from agentcli.core.analysis.output_formatter import OutputFormatter


@click.command()
@click.argument("file_path", type=click.Path(exists=True), required=True)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed analysis")
@click.option("--format", "-f", type=click.Choice(["console", "json"]), default="console", 
              help="Output format")
def explain(file_path, verbose, format):
    """Объясняет код из файла с помощью AI анализа.
    
    FILE_PATH - путь к файлу для объяснения.
    """
    console = Console()
    
    # Convert to absolute path
    abs_path = os.path.abspath(file_path)
    
    # Check if it's a Python file
    if not abs_path.endswith('.py'):
        console.print("[red]Error:[/red] Only Python files are currently supported")
        return
    
    try:
        # Initialize components
        analyzer = ModuleAnalyzer()
        summarizer = CodeSummarizer()
        formatter = OutputFormatter()
        
        # Analyze the module
        with console.status("Analyzing module structure..."):
            module_info = analyzer.analyze_file(abs_path)
        
        if not module_info:
            console.print(f"[red]Error:[/red] Failed to analyze {file_path}")
            return
        
        # Generate summary and insights
        with console.status("Generating AI-powered summary..."):
            analysis_result = summarizer.summarize_module(module_info)
        
        # Format and display results
        if format == "console":
            formatter.format_analysis(analysis_result, verbose=verbose)
        elif format == "json":
            import json
            # Convert to JSON (simplified)
            json_data = {
                "module_name": module_info.module_name,
                "file_path": module_info.file_path,
                "summary": analysis_result.summary,
                "complexity_level": analysis_result.complexity_level,
                "classes_count": len(module_info.classes),
                "functions_count": len(module_info.functions),
                "line_count": module_info.line_count,
                "dependencies": analysis_result.dependencies,
                "recommendations": analysis_result.recommendations
            }
            console.print(json.dumps(json_data, indent=2))
        
    except Exception as e:
        console.print(f"[red]Error during analysis:[/red] {str(e)}")
        if verbose:
            console.print_exception()
