"""
Caching utilities for performance optimization.

Provides in-memory caching for expensive operations.
"""

from typing import Any, Callable, Optional, Dict
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import json


class TimedCache:
	"""Simple in-memory cache with TTL."""

	def __init__(self, default_ttl: int = 3600):
		"""
		Initialize cache.
		
		Args:
			default_ttl: Default time-to-live in seconds
		"""
		self.cache: Dict[str, tuple[Any, datetime]] = {}
		self.default_ttl = default_ttl

	def get(self, key: str) -> Optional[Any]:
		"""Get value from cache if not expired."""
		if key not in self.cache:
			return None

		value, expiry = self.cache[key]
		if datetime.now() > expiry:
			del self.cache[key]
			return None

		return value

	def set(self, key: str, value: Any, ttl: Optional[int] = None):
		"""Set value in cache with TTL."""
		ttl = ttl or self.default_ttl
		expiry = datetime.now() + timedelta(seconds=ttl)
		self.cache[key] = (value, expiry)

	def clear(self):
		"""Clear all cache entries."""
		self.cache.clear()


# Global cache instance
_cache = TimedCache()


def cached(
	ttl: int = 3600,
	key_func: Optional[Callable] = None,
):
	"""
	Decorator for caching function results.
	
	Args:
		ttl: Time-to-live in seconds
		key_func: Function to generate cache key from arguments
	"""
	def decorator(func: Callable) -> Callable:
		@wraps(func)
		def wrapper(*args, **kwargs) -> Any:
			# Generate cache key
			if key_func:
				cache_key = key_func(*args, **kwargs)
			else:
				# Default: hash arguments
				key_data = json.dumps(
					{"args": str(args), "kwargs": str(sorted(kwargs.items()))},
					sort_keys=True,
				)
				cache_key = f"{func.__name__}:{hashlib.md5(key_data.encode()).hexdigest()}"

			# Check cache
			cached_value = _cache.get(cache_key)
			if cached_value is not None:
				return cached_value

			# Execute function
			result = func(*args, **kwargs)

			# Store in cache
			_cache.set(cache_key, result, ttl)

			return result

		return wrapper
	return decorator


def clear_cache():
	"""Clear the global cache."""
	_cache.clear()



