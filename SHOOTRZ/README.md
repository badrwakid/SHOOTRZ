# SHOOTRZ

AI-assisted basketball shooting analysis app with React Native (Expo) frontend
and FastAPI backend.

## Stack

- Frontend: Expo + React Native + TypeScript
- Backend: FastAPI + Python
- Core analysis: deterministic pipeline in `backend/mvp/core`
- Data/Auth: Supabase integrations

## Canonical Run Commands

Run from `SHOOTRZ/`:

```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

In another terminal:

```bash
npm install
npm start
```

## Architecture

- API: `backend/routers`, entry `backend/main.py`
- MVP pipeline: `backend/mvp/core/pipeline.py`
- Contracts: `backend/contracts`, `src/types/contracts`

## MVP-Critical Flow

1. Mobile Analyze screen uploads a video (`/mvp/analyze`)
2. Backend job is queued and persisted
3. Pipeline runs in `backend/mvp/core/pipeline.py`
4. Mobile polls `/mvp/result/{job_id}`
5. App renders score, metrics, angles, and artifact links

## Testing

Backend targeted validation:

```bash
cd backend
python -m pytest tests/test_api_contracts.py tests/test_job_store.py -q
```

MVP pipeline tests:

```bash
cd backend
python -m pytest mvp/tests -q
```
