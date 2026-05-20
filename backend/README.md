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
