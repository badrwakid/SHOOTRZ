# SHOOTRZ API Documentation

## Base URL
- Development: `http://127.0.0.1:8000`
- Production: `https://api.shootrz.com` (update with your domain)

## Authentication
All endpoints require user authentication via Supabase JWT tokens in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Endpoints

### POST /analyze
Upload and analyze a basketball shooting video.

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `file`: Video file (required if no file_url)
  - `user_id`: User ID (optional)
  - `angle`: Camera angle type (optional)
  - `fps`: Video frame rate (optional)
  - `device`: Device information (optional)
  - `file_url`: Video URL from Supabase Storage (required if no file)

**Response:**
```json
{
  "job_id": "abc123",
  "status": "queued"
}
```

### GET /result/{job_id}
Get analysis results for a processing job.

**Response:**
```json
{
  "job_id": "abc123",
  "status": "completed",
  "metrics": [...],
  "feedback": [...],
  "phases": [...],
  "video_id": "video-uuid"
}
```

### GET /result/{job_id}/status
Get only the status of a job (lightweight polling endpoint).

**Response:**
```json
{
  "job_id": "abc123",
  "status": "processing"
}
```

### GET /history/{user_id}
Get user's analysis history with sessions.

**Query Parameters:**
- `limit`: Maximum sessions to return (default: 50)
- `offset`: Pagination offset (default: 0)
- `start_date`: Filter from date (ISO format)
- `end_date`: Filter to date (ISO format)

**Response:**
```json
{
  "user_id": "user-uuid",
  "sessions": [...],
  "total": 10
}
```

### GET /history/{user_id}/stats
Get aggregated statistics from user's history.

**Response:**
```json
{
  "total_sessions": 10,
  "total_shots": 10,
  "average_score": 75.5,
  "best_score": 92.3,
  "improvement_percentage": 15.2,
  "consistency_score": 82.1
}
```

### POST /sessions/{user_id}
Create a new practice session.

**Body:**
```json
{
  "title": "Practice Session 1",
  "date": "2024-01-15"
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "SHOOTRZ FastAPI Backend",
  "version": "1.0.0",
  "uptime": 3600.5
}
```

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error message"
}
```

Status codes:
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error



