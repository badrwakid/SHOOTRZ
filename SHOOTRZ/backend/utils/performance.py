"""
Performance monitoring and optimization utilities.

Provides timing, profiling, and performance metrics.
"""

import time
import functools
from typing import Callable, Dict, Any
from collections import defaultdict

_performance_stats: Dict[str, list] = defaultdict(list)


def timeit(func: Callable) -> Callable:
	"""Decorator to measure function execution time."""
	@functools.wraps(func)
	def wrapper(*args, **kwargs) -> Any:
		start = time.time()
		result = func(*args, **kwargs)
		elapsed = time.time() - start
		
		# Store timing
		_performance_stats[func.__name__].append(elapsed)
		
		return result
	return wrapper


def get_performance_stats() -> Dict[str, Dict[str, float]]:
	"""
	Get performance statistics for all timed functions.
	
	Returns:
		Dict with function names and statistics (mean, min, max, count)
	"""
	stats = {}
	for func_name, times in _performance_stats.items():
		if times:
			stats[func_name] = {
				"mean": sum(times) / len(times),
				"min": min(times),
				"max": max(times),
				"count": len(times),
			}
	return stats


def reset_performance_stats():
	"""Reset performance statistics."""
	_performance_stats.clear()



