"""
Request logging middleware for FastAPI.

Logs all API requests with timing and error information.
"""

import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
	"""Middleware to log all HTTP requests."""

	async def dispatch(self, request: Request, call_next):
		"""Process request and log details."""
		start_time = time.time()
		
		# Log request
		logger.info(
			f"{request.method} {request.url.path} - "
			f"Client: {request.client.host if request.client else 'unknown'}"
		)
		
		try:
			response = await call_next(request)
			process_time = time.time() - start_time
			
			# Log response
			logger.info(
				f"{request.method} {request.url.path} - "
				f"Status: {response.status_code} - "
				f"Time: {process_time:.3f}s"
			)
			
			# Add timing header
			response.headers["X-Process-Time"] = str(process_time)
			
			return response
		except Exception as e:
			process_time = time.time() - start_time
			logger.error(
				f"{request.method} {request.url.path} - "
				f"Error: {str(e)} - "
				f"Time: {process_time:.3f}s"
			)
			raise



