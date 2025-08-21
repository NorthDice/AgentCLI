"""Metrics analysis and reporting utilities."""

import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .models import OperationMetrics


class MetricsAnalyzer:
    """Analyzer for performance metrics data."""
    
    def __init__(self, metrics: List[OperationMetrics]):
        self.metrics = metrics
    
    def analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        if not self.metrics:
            return {"message": "No metrics to analyze"}
        
        # Sort by time
        sorted_metrics = sorted(self.metrics, key=lambda m: m.start_time)
        
        durations = [m.duration for m in sorted_metrics]
        memory_deltas = [m.memory_delta_mb for m in sorted_metrics]
        
        return {
            "total_operations": len(self.metrics),
            "time_range": {
                "start": datetime.fromtimestamp(sorted_metrics[0].start_time).isoformat(),
                "end": datetime.fromtimestamp(sorted_metrics[-1].start_time).isoformat(),
                "duration_hours": (sorted_metrics[-1].start_time - sorted_metrics[0].start_time) / 3600
            },
            "performance_stats": {
                "avg_duration": statistics.mean(durations),
                "median_duration": statistics.median(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "duration_std": statistics.stdev(durations) if len(durations) > 1 else 0
            },
            "memory_stats": {
                "avg_memory_delta": statistics.mean(memory_deltas),
                "median_memory_delta": statistics.median(memory_deltas),
                "total_memory_used": sum(max(0, delta) for delta in memory_deltas),
                "memory_leaks_detected": len([d for d in memory_deltas if d > 50])  # >50MB growth
            },
            "success_rate": len([m for m in self.metrics if m.success]) / len(self.metrics) * 100
        }
    
    def get_operation_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get performance breakdown by operation type."""
        operation_groups = {}
        
        for metric in self.metrics:
            op_type = metric.operation
            if op_type not in operation_groups:
                operation_groups[op_type] = []
            operation_groups[op_type].append(metric)
        
        breakdown = {}
        for op_type, ops in operation_groups.items():
            durations = [m.duration for m in ops]
            memory_deltas = [m.memory_delta_mb for m in ops]
            
            breakdown[op_type] = {
                "count": len(ops),
                "success_rate": len([m for m in ops if m.success]) / len(ops) * 100,
                "avg_duration": statistics.mean(durations),
                "total_duration": sum(durations),
                "avg_memory_delta": statistics.mean(memory_deltas),
                "total_items_processed": sum(m.items_processed for m in ops),
                "performance_rating": self._calculate_performance_rating(durations, memory_deltas)
            }
        
        return breakdown
    
    def _calculate_performance_rating(self, durations: List[float], memory_deltas: List[float]) -> str:
        """Calculate overall performance rating."""
        avg_duration = statistics.mean(durations)
        avg_memory = statistics.mean(memory_deltas)
        
        if avg_duration < 0.1 and avg_memory < 10:
            return "excellent"
        elif avg_duration < 1.0 and avg_memory < 50:
            return "good"
        elif avg_duration < 5.0 and avg_memory < 100:
            return "fair"
        else:
            return "poor"
    
    def detect_performance_issues(self) -> List[Dict[str, Any]]:
        """Detect potential performance issues."""
        issues = []
        
        # Check for slow operations
        slow_ops = [m for m in self.metrics if m.duration > 5.0]
        if slow_ops:
            issues.append({
                "type": "slow_operations",
                "count": len(slow_ops),
                "description": f"{len(slow_ops)} operations took longer than 5 seconds",
                "severity": "high" if len(slow_ops) > len(self.metrics) * 0.2 else "medium"
            })
        
        # Check for memory leaks
        memory_leaks = [m for m in self.metrics if m.memory_delta_mb > 100]
        if memory_leaks:
            issues.append({
                "type": "memory_leaks",
                "count": len(memory_leaks),
                "description": f"{len(memory_leaks)} operations used more than 100MB",
                "severity": "high"
            })
        
        # Check for high failure rate
        failed_ops = [m for m in self.metrics if not m.success]
        failure_rate = len(failed_ops) / len(self.metrics) * 100 if self.metrics else 0
        if failure_rate > 10:
            issues.append({
                "type": "high_failure_rate",
                "failure_rate": failure_rate,
                "description": f"Failure rate is {failure_rate:.1f}% (above 10% threshold)",
                "severity": "high" if failure_rate > 25 else "medium"
            })
        
        return issues
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        return {
            "summary": self.analyze_performance_trends(),
            "operation_breakdown": self.get_operation_breakdown(),
            "issues": self.detect_performance_issues(),
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        issues = self.detect_performance_issues()
        
        for issue in issues:
            if issue["type"] == "slow_operations":
                recommendations.append("Consider optimizing slow operations or adding caching")
            elif issue["type"] == "memory_leaks":
                recommendations.append("Review memory usage patterns and implement cleanup")
            elif issue["type"] == "high_failure_rate":
                recommendations.append("Investigate and fix failing operations")
        
        if not issues:
            recommendations.append("Performance looks good! No major issues detected.")
        
        return recommendations
