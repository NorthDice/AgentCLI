"""
Data models for performance metrics.

This module defines the core data structures used for tracking
performance metrics across different operations in AgentCLI.
"""

import time
from dataclasses import dataclass, asdict
from typing import Dict, Optional, Any
from datetime import datetime


@dataclass
class OperationMetrics:
    """Base metrics for any operation in AgentCLI."""
    
    operation: str
    start_time: float
    end_time: float
    duration: float
    memory_before_mb: float
    memory_after_mb: float
    memory_delta_mb: float
    cpu_percent: float
    items_processed: int
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return asdict(self)
    
    def get_timestamp(self) -> str:
        """Get human-readable timestamp."""
        return datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%d %H:%M:%S")
    
    @property
    def memory_efficiency(self) -> str:
        """Calculate memory efficiency rating."""
        if self.memory_delta_mb < 10:
            return "excellent"
        elif self.memory_delta_mb < 50:
            return "good"
        elif self.memory_delta_mb < 100:
            return "fair"
        else:
            return "poor"
    
    @property
    def speed_rating(self) -> str:
        """Calculate speed rating based on duration."""
        if self.duration < 0.1:
            return "very_fast"
        elif self.duration < 1.0:
            return "fast"
        elif self.duration < 5.0:
            return "moderate"
        else:
            return "slow"


@dataclass
class SearchMetrics(OperationMetrics):
    """Specialized metrics for search operations."""
    
    query: str = ""
    results_found: int = 0
    index_size: int = 0
    embedding_time: float = 0.0
    vector_search_time: float = 0.0
    
    @property
    def results_per_second(self) -> float:
        """Calculate results processed per second."""
        return self.results_found / self.duration if self.duration > 0 else 0
    
    @property
    def embedding_efficiency(self) -> str:
        """Rate embedding generation efficiency."""
        if self.embedding_time < 0.05:
            return "excellent"
        elif self.embedding_time < 0.2:
            return "good"
        elif self.embedding_time < 0.5:
            return "fair"
        else:
            return "poor"


@dataclass
class IndexingMetrics(OperationMetrics):
    """Specialized metrics for indexing operations."""
    
    files_processed: int = 0
    chunks_created: int = 0
    embedding_generation_time: float = 0.0
    vector_store_time: float = 0.0
    
    @property
    def files_per_second(self) -> float:
        """Calculate files processed per second."""
        return self.files_processed / self.duration if self.duration > 0 else 0
    
    @property
    def chunks_per_second(self) -> float:
        """Calculate chunks processed per second."""
        return self.chunks_created / self.duration if self.duration > 0 else 0
    
    @property
    def indexing_efficiency(self) -> str:
        """Rate overall indexing efficiency."""
        files_rate = self.files_per_second
        if files_rate > 10:
            return "excellent"
        elif files_rate > 5:
            return "good"
        elif files_rate > 1:
            return "fair"
        else:
            return "poor"


@dataclass
class SystemMetrics:
    """System-wide performance metrics."""
    
    timestamp: float
    total_memory_mb: float
    available_memory_mb: float
    cpu_usage_percent: float
    disk_usage_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @property
    def memory_usage_percent(self) -> float:
        """Calculate memory usage percentage."""
        used = self.total_memory_mb - self.available_memory_mb
        return (used / self.total_memory_mb * 100) if self.total_memory_mb > 0 else 0
    
    @property
    def system_health(self) -> str:
        """Overall system health rating."""
        if self.cpu_usage_percent < 50 and self.memory_usage_percent < 70:
            return "healthy"
        elif self.cpu_usage_percent < 80 and self.memory_usage_percent < 85:
            return "moderate"
        else:
            return "stressed"
