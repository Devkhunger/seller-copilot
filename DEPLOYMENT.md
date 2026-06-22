# Deployment Guide

## What to deploy

This app has two services:

- Backend API: FastAPI in `backend/`
- Frontend web app: Vite/React in `frontend/`

The frontend must know the backend URL through `VITE_API_BASE`.
The backend must allow the frontend URL through `FRONTEND_ORIGINS`.

## Option 1: Local production Docker

From `seller-copilot/`:

```bash
docker compose up --build
```

Open:

```text
http://localhost:8080
```

Backend health:

```text
http://localhost:8000/api/health
```

SQLite data is stored in the Docker volume `seller_data`.

## Option 2: Render

A `render.yaml` file is included for two Render services:

- `seller-copilot-api`
- `seller-copilot-web`

Steps:

1. Push this project to GitHub.
2. In Render, create a Blueprint from the repo.
3. Deploy the backend first and copy its URL.
4. Set frontend env var:

```text
VITE_API_BASE=https://YOUR-BACKEND-URL
```

5. Set backend env var:

```text
FRONTEND_ORIGINS=https://YOUR-FRONTEND-URL
```

6. Optional backend env vars:

```text
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-5.2
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash
```

The backend uses a persistent disk at `/var/data` for SQLite.

## Option 3: Vercel frontend + Render backend

Backend on Render:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Frontend on Vercel:

```text
Build command: npm run build
Output directory: dist
Root directory: frontend
Environment: VITE_API_BASE=https://YOUR-BACKEND-URL
Also set: VITE_GOOGLE_CLIENT_ID=your_google_oauth_client_id
```

Backend CORS:

```text
FRONTEND_ORIGINS=https://YOUR-VERCEL-URL
GOOGLE_CLIENT_ID=your_google_oauth_client_id
```

## Production notes

For a real business deployment, move from SQLite to PostgreSQL before multiple sellers use the same app. SQLite is fine for MVP/demo and single-seller use, but not ideal for many concurrent users.
