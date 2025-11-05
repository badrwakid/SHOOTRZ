# ✅ Fixed: Backend Start Command

## Problem
When running from `SHOOTRZ\backend` directory, you get:
```
ImportError: attempted relative import with no known parent package
```

This happens because `main.py` uses relative imports (`from .routers import ...`).

## Solution: Run from Parent Directory

### From `D:\myprojects\Grad` directory:

```powershell
cd D:\myprojects\Grad
uvicorn SHOOTRZ.backend.main:app --reload --host 0.0.0.0 --port 8000
```

**OR if using factory pattern:**

```powershell
cd D:\myprojects\Grad
uvicorn SHOOTRZ.backend.main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

## Verify Success

After starting, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**NOT** `http://127.0.0.1:8000`!

## Test from iPhone

1. Open Safari on iPhone
2. Navigate to: `http://192.168.1.4:8000/health`
3. Should see: `{"status":"healthy",...}`

## Why This Works

- Running from `Grad` directory treats `SHOOTRZ` as a proper Python package
- The relative imports in `main.py` work correctly
- `--host 0.0.0.0` makes it accessible from network devices



