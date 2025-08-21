"""Metrics collection and context management."""

import time
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager

from .models import OperationMetrics, SystemMetrics
from .monitoring import ResourceMonitor

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Central metrics collection service."""
    
    def __init__(self):
        self.metrics: List[OperationMetrics] = []
        self.session_start_time = time.time()
        self.metrics_file = ".agentcli/metrics/session_metrics.json"
        self.resource_monitor = ResourceMonitor()
        self._ensure_metrics_dir()
        self._load_existing_metrics()
    
    def _ensure_metrics_dir(self):
        """Ensure metrics directory exists."""
        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
    
    def _load_existing_metrics(self):
        """Load existing metrics from file."""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    
                # Load session start time
                if 'session_start_time' in data:
                    self.session_start_time = data['session_start_time']
                
                # Load metrics
                if 'metrics' in data:
                    for metric_data in data['metrics']:
                        # Convert dict back to OperationMetrics
                        metric = OperationMetrics(
                            operation=metric_data['operation'],
                            start_time=metric_data['start_time'],
                            end_time=metric_data['end_time'],
                            duration=metric_data['duration'],
                            memory_before_mb=metric_data['memory_before_mb'],
                            memory_after_mb=metric_data['memory_after_mb'],
                            memory_delta_mb=metric_data['memory_delta_mb'],
                            cpu_percent=metric_data['cpu_percent'],
                            items_processed=metric_data['items_processed'],
                            success=metric_data['success'],
                            error_message=metric_data.get('error_message')
                        )
                        self.metrics.append(metric)
                        
            except Exception as e:
                logger.error(f"Failed to load existing metrics: {e}")
    
    def _save_metrics(self):
        """Save metrics to file."""
        try:
            data = {
                'session_start_time': self.session_start_time,
                'last_updated': time.time(),
                'metrics': [metric.to_dict() for metric in self.metrics]
            }
            
            with open(self.metrics_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def start_operation(self, operation: str, **kwargs) -> 'OperationContext':
        """Start measuring an operation."""
        return OperationContext(self, operation, **kwargs)
    
    def record_metric(self, metric: OperationMetrics):
        """Record a completed metric."""
        self.metrics.append(metric)
        self._save_metrics()
        logger.debug(f"Recorded metric: {metric.operation} - {metric.duration:.3f}s")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get comprehensive session statistics."""
        if not self.metrics:
            return {"message": "No metrics recorded"}
        
        # Filter metrics by type
        search_metrics = [m for m in self.metrics if 'search' in m.operation.lower()]
        index_metrics = [m for m in self.metrics if 'index' in m.operation.lower()]
        all_successful = [m for m in self.metrics if m.success]
        
        return {
            "session_duration": time.time() - self.session_start_time,
            "total_operations": len(self.metrics),
            "successful_operations": len(all_successful),
            "failed_operations": len(self.metrics) - len(all_successful),
            "search_operations": len(search_metrics),
            "indexing_operations": len(index_metrics),
            "avg_search_time": self._safe_average([m.duration for m in search_metrics]),
            "avg_index_time": self._safe_average([m.duration for m in index_metrics]),
            "avg_operation_time": self._safe_average([m.duration for m in self.metrics]),
            "total_memory_used": sum(max(0, m.memory_delta_mb) for m in self.metrics),
            "peak_memory_usage": max((m.memory_after_mb for m in self.metrics), default=0),
            "avg_cpu_usage": self._safe_average([m.cpu_percent for m in self.metrics]),
            "total_items_processed": sum(m.items_processed for m in self.metrics)
        }
    
    def _safe_average(self, values: List[float]) -> float:
        """Calculate average safely handling empty lists."""
        return sum(values) / len(values) if values else 0.0
    
    def clear_metrics(self):
        """Clear all stored metrics."""
        self.metrics.clear()
        self._save_metrics()
    
    def get_session_stats(self):
        """Get comprehensive session statistics."""
        if not self.metrics:
            return {"message": "No metrics recorded in this session"}
        
        now = time.time()
        session_duration = now - self.session_start_time
        
        # Basic counts
        total_operations = len(self.metrics)
        successful_operations = len([m for m in self.metrics if m.success])
        failed_operations = total_operations - successful_operations
        
        # Operation type counts
        search_operations = len([m for m in self.metrics if 'search' in m.operation.lower()])
        indexing_operations = len([m for m in self.metrics if 'index' in m.operation.lower()])
        
        # Performance metrics
        avg_operation_time = sum(m.duration for m in self.metrics) / total_operations
        avg_search_time = (sum(m.duration for m in self.metrics if 'search' in m.operation.lower()) / search_operations) if search_operations > 0 else 0
        avg_index_time = (sum(m.duration for m in self.metrics if 'index' in m.operation.lower()) / indexing_operations) if indexing_operations > 0 else 0
        
        # Resource usage
        total_memory_used = sum(max(0, m.memory_delta_mb) for m in self.metrics)
        peak_memory_usage = max((m.memory_after_mb for m in self.metrics), default=0)
        avg_cpu_usage = sum(m.cpu_percent for m in self.metrics) / total_operations if total_operations > 0 else 0
        
        # Items processed
        total_items_processed = sum(m.items_processed for m in self.metrics)
        
        return {
            "session_duration": session_duration,
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "search_operations": search_operations,
            "indexing_operations": indexing_operations,
            "avg_operation_time": avg_operation_time,
            "avg_search_time": avg_search_time,
            "avg_index_time": avg_index_time,
            "total_memory_used": total_memory_used,
            "peak_memory_usage": peak_memory_usage,
            "avg_cpu_usage": avg_cpu_usage,
            "total_items_processed": total_items_processed
        }
    
    def get_recent_metrics(self, limit: int = 10) -> List[OperationMetrics]:
        """Get most recent metrics."""
        return self.metrics[-limit:] if self.metrics else []
    
    def get_metrics_by_operation(self, operation_pattern: str) -> List[OperationMetrics]:
        """Get metrics filtered by operation pattern."""
        return [m for m in self.metrics 
                if operation_pattern.lower() in m.operation.lower()]


class OperationContext:
    """Context manager for measuring operations."""
    
    def __init__(self, collector: MetricsCollector, operation: str, **kwargs):
        self.collector = collector
        self.operation = operation
        self.kwargs = kwargs
        self.start_time: Optional[float] = None
        self.start_memory: Optional[float] = None
        self.start_cpu: Optional[float] = None
        self.success = True
        self.error_message: Optional[str] = None
        
    def __enter__(self):
        """Start the operation measurement."""
        self.start_time = time.time()
        monitor = self.collector.resource_monitor
        self.start_memory = monitor.get_current_memory_mb()
        self.start_cpu = monitor.get_current_cpu_percent()
        
        logger.debug(f"Started measuring operation: {self.operation}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Complete the operation measurement and record metrics."""
        if self.start_time is None:
            logger.warning("Operation context exited without entering")
            return
            
        end_time = time.time()
        monitor = self.collector.resource_monitor
        end_memory = monitor.get_current_memory_mb()
        end_cpu = monitor.get_current_cpu_percent()
        
        # Handle exceptions
        if exc_type is not None:
            self.success = False
            self.error_message = str(exc_val) if exc_val else f"{exc_type.__name__}"
        
        # Create metrics record
        metric = OperationMetrics(
            operation=self.operation,
            start_time=self.start_time,
            end_time=end_time,
            duration=end_time - self.start_time,
            memory_before_mb=self.start_memory,
            memory_after_mb=end_memory,
            memory_delta_mb=end_memory - self.start_memory,
            cpu_percent=(self.start_cpu + end_cpu) / 2,  # Average CPU usage
            items_processed=self.kwargs.get('items_processed', 1),
            success=self.success,
            error_message=self.error_message
        )
        
        self.collector.record_metric(metric)
        
        log_level = logging.INFO if self.success else logging.WARNING
        logger.log(log_level, 
                  f"Operation '{self.operation}' completed: "
                  f"{metric.duration:.3f}s, "
                  f"{metric.memory_delta_mb:+.1f}MB, "
                  f"success={self.success}")
    
    def update_items_processed(self, count: int):
        """Update the number of items processed during the operation."""
        self.kwargs['items_processed'] = count
    
    def add_custom_data(self, **data):
        """Add custom data to the operation context."""
        self.kwargs.update(data)


# Global metrics collector instance
metrics_collector = MetricsCollector()


@contextmanager
def measure_operation(operation_name: str, **kwargs):
    """Convenience context manager for measuring operations."""
    with metrics_collector.start_operation(operation_name, **kwargs) as ctx:
        yield ctx
