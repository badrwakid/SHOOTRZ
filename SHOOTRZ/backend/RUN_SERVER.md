# How to Run the Backend Server

## ✅ Correct Command

Run from the **SHOOTRZ directory** (parent of backend):

```bash
cd d:\Users\Badr\myprojects\Grad\SHOOTRZ
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**NOT from inside the backend directory** - this causes import errors.

**Important:** Use `--host 0.0.0.0` to allow connections from physical devices on your network. Without this, the server only accepts localhost connections.

## Why This Works

The `backend` module needs to be importable as a package. When you run from `SHOOTRZ/`, Python can find `backend.main:app` because:
- `SHOOTRZ/` is in the Python path
- `backend/` is a package (has `__init__.py`)
- `backend.main` resolves correctly

## Verify Server is Running

```bash
# Check health
curl http://127.0.0.1:8000/health

# Or in PowerShell
Invoke-WebRequest http://127.0.0.1:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "SHOOTRZ FastAPI Backend",
  "version": "1.0.0"
}
```

## View API Documentation

Open in browser: http://127.0.0.1:8000/docs

You should see:
- `/health` endpoint
- `/mvp/analyze` endpoint
- `/mvp/result/{job_id}` endpoint
- `/mvp/artifacts/{run_id}/{filename}` endpoint

## Troubleshooting

### Error: `ModuleNotFoundError: No module named 'backend'`
**Solution:** Run from `SHOOTRZ/` directory, not `SHOOTRZ/backend/`

### Error: `Fatal error in launcher: Unable to create process`
**Solution:** Use `python -m uvicorn` instead of just `uvicorn`


