"""
System resource monitoring utilities.

This module provides utilities for monitoring system resources
like memory, CPU, and disk usage during AgentCLI operations.
"""

import psutil
import time
from typing import Dict, Any
from .models import SystemMetrics


class ResourceMonitor:
    """Monitor system resources during operations."""
    
    def __init__(self):
        self.process = psutil.Process()
        self._baseline_memory = None
        self._baseline_cpu = None
    
    def get_current_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
    
    def get_current_cpu_percent(self) -> float:
        """Get current CPU usage percentage."""
        return self.process.cpu_percent()
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get comprehensive system metrics."""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return SystemMetrics(
            timestamp=time.time(),
            total_memory_mb=memory.total / 1024 / 1024,
            available_memory_mb=memory.available / 1024 / 1024,
            cpu_usage_percent=psutil.cpu_percent(interval=0.1),
            disk_usage_percent=disk.percent
        )
    
    def set_baseline(self):
        """Set baseline measurements for delta calculations."""
        self._baseline_memory = self.get_current_memory_mb()
        self._baseline_cpu = self.get_current_cpu_percent()
    
    def get_memory_delta(self) -> float:
        """Get memory change since baseline."""
        if self._baseline_memory is None:
            return 0.0
        return self.get_current_memory_mb() - self._baseline_memory
    
    def get_cpu_average(self) -> float:
        """Get average CPU usage since baseline."""
        if self._baseline_cpu is None:
            return self.get_current_cpu_percent()
        return (self._baseline_cpu + self.get_current_cpu_percent()) / 2
    
    def reset_baseline(self):
        """Reset baseline measurements."""
        self._baseline_memory = None
        self._baseline_cpu = None


class PerformanceTimer:
    """High-precision timer for performance measurements."""
    
    def __init__(self):
        self._start_time = None
        self._end_time = None
        self._checkpoints = {}
    
    def start(self):
        """Start timing."""
        self._start_time = time.perf_counter()
        self._end_time = None
        self._checkpoints.clear()
    
    def stop(self) -> float:
        """Stop timing and return duration."""
        if self._start_time is None:
            raise ValueError("Timer not started")
        
        self._end_time = time.perf_counter()
        return self.get_duration()
    
    def checkpoint(self, name: str) -> float:
        """Create a named checkpoint and return time since start."""
        if self._start_time is None:
            raise ValueError("Timer not started")
        
        current_time = time.perf_counter()
        elapsed = current_time - self._start_time
        self._checkpoints[name] = elapsed
        return elapsed
    
    def get_duration(self) -> float:
        """Get total duration."""
        if self._start_time is None:
            return 0.0
        
        end_time = self._end_time or time.perf_counter()
        return end_time - self._start_time
    
    def get_checkpoint_duration(self, name: str) -> float:
        """Get time at specific checkpoint."""
        return self._checkpoints.get(name, 0.0)
    
    def get_checkpoint_delta(self, start_checkpoint: str, end_checkpoint: str) -> float:
        """Get time difference between two checkpoints."""
        start_time = self._checkpoints.get(start_checkpoint, 0.0)
        end_time = self._checkpoints.get(end_checkpoint, 0.0)
        return end_time - start_time
    
    @property
    def checkpoints(self) -> Dict[str, float]:
        """Get all checkpoints."""
        return self._checkpoints.copy()
