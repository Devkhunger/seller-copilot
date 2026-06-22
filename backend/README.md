# Backend

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`.

Optional env vars for trend-aware listing generation:

- `GEMINI_API_KEY`
- `GEMINI_MODEL`

When configured, Gemini generates the candidate keyword phrases and `pytrends` ranks them for Listing Doctor.
If these are missing, Listing Doctor falls back to the local keyword generator.

## Endpoints

- `POST /api/upload`
- `GET /api/dashboard`
- `GET /api/sku-scores`
- `GET /api/rto-risk`
- `GET /api/recommendations`
- `POST /api/listing-doctor`
- `GET /api/inventory`
- `POST /api/inventory`
- `POST /api/actions/{id}/done`
- `GET /api/usage`

