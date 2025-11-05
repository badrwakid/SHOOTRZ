"""
Comprehensive error handling and logging utilities.

Provides retry logic, error recovery, and detailed error reporting.
"""

import logging
import traceback
from typing import Callable, Any, Optional, TypeVar, List
from functools import wraps
from time import sleep

T = TypeVar("T")

logger = logging.getLogger(__name__)


def retry(
	max_attempts: int = 3,
	delay: float = 1.0,
	exceptions: tuple = (Exception,),
	backoff: float = 2.0,
):
	"""
	Decorator for retrying functions with exponential backoff.
	
	Args:
		max_attempts: Maximum number of retry attempts
		delay: Initial delay between retries (seconds)
		exceptions: Tuple of exceptions to catch and retry on
		backoff: Multiplier for delay on each retry
	"""
	def decorator(func: Callable[..., T]) -> Callable[..., T]:
		@wraps(func)
		def wrapper(*args, **kwargs) -> T:
			current_delay = delay
			last_exception = None

			for attempt in range(max_attempts):
				try:
					return func(*args, **kwargs)
				except exceptions as e:
					last_exception = e
					if attempt < max_attempts - 1:
						logger.warning(
							f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}. "
							f"Retrying in {current_delay}s..."
						)
						sleep(current_delay)
						current_delay *= backoff
					else:
						logger.error(f"{func.__name__} failed after {max_attempts} attempts")
			
			raise last_exception
		return wrapper
	return decorator


def handle_processing_error(
	error: Exception,
	context: str = "",
	return_default: Any = None,
) -> Any:
	"""
	Handle processing errors with logging and graceful degradation.
	
	Args:
		error: The exception that occurred
		context: Context description for logging
		return_default: Default value to return on error
	
	Returns:
		Default value or re-raises error
	"""
	logger.error(f"Error in {context}: {error}")
	logger.debug(traceback.format_exc())
	
	if return_default is not None:
		return return_default
	raise error


def validate_video_file(video_path: str) -> tuple[bool, Optional[str]]:
	"""
	Validate video file before processing.
	
	Args:
		video_path: Path to video file
	
	Returns:
		Tuple of (is_valid, error_message)
	"""
	from pathlib import Path
	import cv2

	path = Path(video_path)
	
	if not path.exists():
		return False, f"Video file not found: {video_path}"
	
	if not path.is_file():
		return False, f"Path is not a file: {video_path}"
	
	# Try to open video
	try:
		cap = cv2.VideoCapture(str(video_path))
		if not cap.isOpened():
			return False, "Could not open video file"
		
		frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
		fps = cap.get(cv2.CAP_PROP_FPS)
		cap.release()
		
		if frame_count == 0:
			return False, "Video has no frames"
		
		if fps <= 0:
			return False, "Invalid frame rate"
		
		return True, None
	except Exception as e:
		return False, f"Error validating video: {str(e)}"


def safe_process(
	func: Callable[..., T],
	*args,
	default: Optional[T] = None,
	log_errors: bool = True,
	**kwargs,
) -> Optional[T]:
	"""
	Safely execute a function with error handling.
	
	Args:
		func: Function to execute
		*args: Positional arguments
		default: Default value to return on error
		log_errors: Whether to log errors
		**kwargs: Keyword arguments
	
	Returns:
		Function result or default value
	"""
	try:
		return func(*args, **kwargs)
	except Exception as e:
		if log_errors:
			logger.error(f"Error in {func.__name__}: {e}")
			logger.debug(traceback.format_exc())
		return default



