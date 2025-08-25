"""Metrics command for performance monitoring and statistics."""

import click
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from datetime import datetime


@click.group()
def metrics():
    """Performance metrics and statistics."""
    pass


@metrics.command()
def show():
    try:
        from agentcli.core.performance.collector import metrics_collector
    except ImportError:
        click.echo("Performance metrics not available")
        return
    
    console = Console()
    stats = metrics_collector.get_session_stats()
    
    if "message" in stats:
        console.print(f"[yellow]{stats['message']}[/yellow]")
        return
    
    table = Table(title="📊 Session Performance Metrics", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    table.add_column("Details", style="dim")

    table.add_row("Session Duration", f"{stats['session_duration']:.1f}s", "Total session time")
    table.add_row("Total Operations", str(stats['total_operations']), "All recorded operations")
    table.add_row("Success Rate", f"{(stats['successful_operations']/stats['total_operations']*100):.1f}%", f"{stats['successful_operations']}/{stats['total_operations']} successful")
    
    table.add_row("", "", "")  

    table.add_row("Avg Operation Time", f"{stats['avg_operation_time']:.3f}s", "Average across all operations")
    table.add_row("Avg Search Time", f"{stats['avg_search_time']:.3f}s", f"Based on {stats['search_operations']} searches")
    table.add_row("Avg Index Time", f"{stats['avg_index_time']:.3f}s", f"Based on {stats['indexing_operations']} operations")
    
    table.add_row("", "", "") 
    
    table.add_row("Total Memory Used", f"{stats['total_memory_used']:.2f} MB", "Total positive memory delta")
    table.add_row("Peak Memory Usage", f"{stats['peak_memory_usage']:.2f} MB", "Highest memory point")
    table.add_row("Avg CPU Usage", f"{stats['avg_cpu_usage']:.1f}%", "Average CPU utilization")
    
    table.add_row("", "", "")  

    table.add_row("Items Processed", str(stats['total_items_processed']), "Total files/results processed")
    table.add_row("Failed Operations", str(stats['failed_operations']), "Operations that failed")
    
    console.print(table)
    

    if stats['total_operations'] > 0:
        avg_time = stats['avg_operation_time']
        if avg_time < 0.5:
            perf_rating = "[green]🚀 Excellent[/green]"
            perf_desc = "Operations are running very fast"
        elif avg_time < 2.0:
            perf_rating = "[yellow]⚡ Good[/yellow]"
            perf_desc = "Operations are running at good speed"
        elif avg_time < 5.0:
            perf_rating = "[orange1]⏱️  Moderate[/orange1]"
            perf_desc = "Operations could be faster"
        else:
            perf_rating = "[red]🐌 Slow[/red]"
            perf_desc = "Operations are running slowly"
        
        total_memory = stats['total_memory_used']
        if total_memory < 50:
            mem_rating = "[green]💾 Low[/green]"
            mem_desc = "Memory usage is efficient"
        elif total_memory < 200:
            mem_rating = "[yellow]📈 Moderate[/yellow]"
            mem_desc = "Memory usage is reasonable"
        else:
            mem_rating = "[red]🔥 High[/red]"
            mem_desc = "Memory usage is high"
        
        perf_panel = Panel(
            f"{perf_rating}\n[dim]{perf_desc}[/dim]",
            title="Performance Rating",
            width=25
        )
        
        mem_panel = Panel(
            f"{mem_rating}\n[dim]{mem_desc}[/dim]",
            title="Memory Usage",
            width=25
        )
        
        console.print("\n")
        console.print(Columns([perf_panel, mem_panel]))


@metrics.command()
@click.option("--operation", help="Filter by operation type")
@click.option("--limit", default=10, help="Number of recent operations to show")
@click.option("--failures-only", is_flag=True, help="Show only failed operations")
def history(operation, limit, failures_only):
    """Show metrics history."""
    try:
        from agentcli.core.performance.collector import metrics_collector
    except ImportError:
        click.echo("Performance metrics not available")
        return
    
    console = Console()

    filtered_metrics = metrics_collector.metrics
    
    if operation:
        filtered_metrics = [m for m in filtered_metrics if operation.lower() in m.operation.lower()]
    
    if failures_only:
        filtered_metrics = [m for m in filtered_metrics if not m.success]
    
    recent_metrics = filtered_metrics[-limit:] if filtered_metrics else []
    
    if not recent_metrics:
        console.print("[yellow]No metrics found matching the criteria[/yellow]")
        return
    
    title = f"📋 Recent Operations (last {len(recent_metrics)})"
    if operation:
        title += f" - filtered by '{operation}'"
    if failures_only:
        title += " - failures only"
    
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("Time", style="cyan", no_wrap=True, width=8)
    table.add_column("Operation", style="green", width=20)
    table.add_column("Duration", style="yellow", justify="right", width=8)
    table.add_column("Memory Δ", style="blue", justify="right", width=10)
    table.add_column("Items", style="magenta", justify="right", width=6)
    table.add_column("Status", style="red", width=6, justify="center")
    table.add_column("Details", style="dim")
    
    for metric in recent_metrics:
        timestamp = datetime.fromtimestamp(metric.start_time).strftime("%H:%M:%S")
        status = "✅" if metric.success else "❌"

        mem_delta = metric.memory_delta_mb
        if mem_delta > 100:
            mem_display = f"[red]+{mem_delta:.1f}MB[/red]"
        elif mem_delta > 10:
            mem_display = f"[yellow]+{mem_delta:.1f}MB[/yellow]"
        elif mem_delta > 0:
            mem_display = f"[green]+{mem_delta:.1f}MB[/green]"
        else:
            mem_display = f"{mem_delta:+.1f}MB"
        
        duration = metric.duration
        if duration > 5:
            dur_display = f"[red]{duration:.3f}s[/red]"
        elif duration > 2:
            dur_display = f"[yellow]{duration:.3f}s[/yellow]"
        else:
            dur_display = f"[green]{duration:.3f}s[/green]"
        
        details = ""
        if metric.error_message:
            details = f"Error: {metric.error_message[:30]}..."
        elif hasattr(metric, 'query'):
            details = f"Query: {getattr(metric, 'query', '')[:20]}..."
        
        table.add_row(
            timestamp,
            metric.operation,
            dur_display,
            mem_display,
            str(metric.items_processed),
            status,
            details
        )
    
    console.print(table)
    
    if len(recent_metrics) > 1:
        avg_duration = sum(m.duration for m in recent_metrics) / len(recent_metrics)
        total_memory = sum(max(0, m.memory_delta_mb) for m in recent_metrics)
        success_rate = len([m for m in recent_metrics if m.success]) / len(recent_metrics) * 100
        
        console.print(f"\n[dim]Summary: Avg duration {avg_duration:.3f}s, "
                     f"Total memory used {total_memory:.1f}MB, "
                     f"Success rate {success_rate:.1f}%[/dim]")


@metrics.command()
def clear():
    """Clear metrics history."""
    try:
        from agentcli.core.performance.collector import metrics_collector
    except ImportError:
        click.echo("Performance metrics not available")
        return
    
    console = Console()

    if not click.confirm("Are you sure you want to clear all metrics history?"):
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    metrics_collector.clear_metrics()
    console.print("[green]✅ Metrics history cleared[/green]")


@metrics.command()
def analyze():
    """Analyze performance patterns and show recommendations."""
    try:
        from agentcli.core.performance.collector import metrics_collector
        from agentcli.core.performance.analytics import MetricsAnalyzer
    except ImportError:
        click.echo("Performance analytics not available")
        return
    
    console = Console()
    
    if not metrics_collector.metrics:
        console.print("[yellow]No metrics data available for analysis[/yellow]")
        return
    
    analyzer = MetricsAnalyzer(metrics_collector.metrics)
    report = analyzer.generate_performance_report()
    
    console.print(Panel.fit(
        f"""[bold green]Performance Analysis Report[/bold green]

            📊 **Overview:**
            • Total Operations: {report['summary']['total_operations']}
            • Time Range: {report['summary']['time_range']['duration_hours']:.1f} hours
            • Success Rate: {report['summary']['success_rate']:.1f}%

            ⏱️  **Performance:**
            • Average Duration: {report['summary']['performance_stats']['avg_duration']:.3f}s
            • Median Duration: {report['summary']['performance_stats']['median_duration']:.3f}s
            • Slowest Operation: {report['summary']['performance_stats']['max_duration']:.3f}s

            💾 **Memory:**
            • Average Memory Delta: {report['summary']['memory_stats']['avg_memory_delta']:.2f}MB
            • Total Memory Used: {report['summary']['memory_stats']['total_memory_used']:.2f}MB
            • Memory Leaks Detected: {report['summary']['memory_stats']['memory_leaks_detected']}
                    """,
                    title="Performance Summary"
            ))

    if report['operation_breakdown']:
        console.print("\n[bold]📋 Operation Breakdown:[/bold]")
        
        breakdown_table = Table(show_header=True, header_style="bold cyan")
        breakdown_table.add_column("Operation", style="green")
        breakdown_table.add_column("Count", justify="right", style="cyan")
        breakdown_table.add_column("Avg Duration", justify="right", style="yellow")
        breakdown_table.add_column("Success Rate", justify="right", style="blue")
        breakdown_table.add_column("Rating", style="magenta")
        
        for op_type, stats in report['operation_breakdown'].items():
            rating_colors = {
                "excellent": "[green]★★★★★[/green]",
                "good": "[yellow]★★★★☆[/yellow]", 
                "fair": "[orange1]★★★☆☆[/orange1]",
                "poor": "[red]★★☆☆☆[/red]"
            }
            rating_display = rating_colors.get(stats['performance_rating'], stats['performance_rating'])
            
            breakdown_table.add_row(
                op_type,
                str(stats['count']),
                f"{stats['avg_duration']:.3f}s",
                f"{stats['success_rate']:.1f}%",
                rating_display
            )
        
        console.print(breakdown_table)
    

    if report['issues']:
        console.print("\n[bold red]⚠️  Issues Detected:[/bold red]")
        for issue in report['issues']:
            severity_colors = {
                "high": "[red]🔴 HIGH[/red]",
                "medium": "[yellow]🟡 MEDIUM[/yellow]",
                "low": "[green]🟢 LOW[/green]"
            }
            severity_display = severity_colors.get(issue['severity'], issue['severity'])
            
            console.print(f"  • {severity_display}: {issue['description']}")
    else:
        console.print("\n[green]✅ No performance issues detected[/green]")

    console.print("\n[bold]💡 Recommendations:[/bold]")
    for rec in report['recommendations']:
        console.print(f"  • {rec}")


@metrics.command()
@click.option("--export-path", default=".agentcli/metrics/export.json", help="Path to export metrics data")
def export(export_path):
    """Export metrics data to JSON file."""
    try:
        from agentcli.core.performance.collector import metrics_collector
        import json
    except ImportError:
        click.echo("Performance metrics not available")
        return
    
    console = Console()
    
    if not metrics_collector.metrics:
        console.print("[yellow]No metrics data to export[/yellow]")
        return

    export_data = {
        "export_timestamp": datetime.now().isoformat(),
        "session_stats": metrics_collector.get_session_stats(),
        "metrics": [metric.to_dict() for metric in metrics_collector.metrics]
    }
    

    os.makedirs(os.path.dirname(export_path), exist_ok=True)

    try:
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        console.print(f"[green]✅ Metrics exported to {export_path}[/green]")
        console.print(f"[dim]Exported {len(export_data['metrics'])} metrics records[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ Export failed: {e}[/red]")


if __name__ == "__main__":
    metrics()
