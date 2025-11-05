"""
API documentation and endpoint documentation generator.
"""

from typing import Dict, List
from pathlib import Path
import json


def generate_api_docs() -> Dict[str, List[Dict]]:
	"""
	Generate API documentation from FastAPI routes.
	
	Returns:
		Dict with endpoint documentation
	"""
	return {
		"endpoints": [
			{
				"path": "/analyze",
				"method": "POST",
				"description": "Upload and analyze basketball shooting video",
				"parameters": {
					"file": "Video file (multipart/form-data)",
					"user_id": "User ID (optional)",
					"angle": "Camera angle type (optional)",
					"fps": "Video frame rate (optional)",
					"device": "Device information (optional)",
					"file_url": "Video URL from Supabase Storage (optional)",
				},
				"response": {
					"job_id": "Processing job ID",
					"status": "Job status (queued/processing/completed/failed)",
				},
			},
			{
				"path": "/result/{job_id}",
				"method": "GET",
				"description": "Get analysis results for a job",
				"parameters": {
					"job_id": "Processing job ID",
				},
				"response": {
					"job_id": "Job ID",
					"status": "Job status",
					"metrics": "List of computed metrics",
					"feedback": "List of feedback messages",
					"phases": "Detected shooting phases",
				},
			},
			{
				"path": "/history/{user_id}",
				"method": "GET",
				"description": "Get user's analysis history",
				"parameters": {
					"user_id": "User ID",
					"limit": "Maximum sessions to return (default: 50)",
					"offset": "Pagination offset (default: 0)",
					"start_date": "Filter from date (ISO format)",
					"end_date": "Filter to date (ISO format)",
				},
				"response": {
					"user_id": "User ID",
					"sessions": "List of sessions with metrics",
					"total": "Total number of sessions",
				},
			},
			{
				"path": "/history/{user_id}/stats",
				"method": "GET",
				"description": "Get aggregated statistics from user's history",
				"response": {
					"total_sessions": "Total number of sessions",
					"average_score": "Average metric score",
					"best_score": "Best metric score",
					"improvement_percentage": "Improvement trend percentage",
					"consistency_score": "Consistency score (0-100)",
				},
			},
			{
				"path": "/sessions/{user_id}",
				"method": "POST",
				"description": "Create a new practice session",
				"parameters": {
					"user_id": "User ID",
					"title": "Session title (optional)",
					"date": "Session date (optional)",
				},
			},
			{
				"path": "/health",
				"method": "GET",
				"description": "Health check endpoint",
				"response": {
					"status": "healthy",
					"service": "SHOOTRZ FastAPI Backend",
					"version": "1.0.0",
				},
			},
		],
	}


def save_api_docs(output_path: Path):
	"""Save API documentation to JSON file."""
	docs = generate_api_docs()
	with open(output_path, "w") as f:
		json.dump(docs, f, indent=2)
	print(f"API documentation saved to: {output_path}")



