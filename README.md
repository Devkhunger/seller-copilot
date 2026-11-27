# AI Seller Copilot for Small E-commerce Sellers

AI Seller Copilot is a full-stack business intelligence MVP designed to help small e-commerce sellers make data-driven decisions using their marketplace order data.

The platform allows sellers to upload order CSV files from Meesho, Flipkart, and Amazon, automatically processes messy marketplace data, and generates actionable business insights.

**What should I do today to increase profitable orders and reduce business losses?**

## Live Demo

**Live Application:** https://seller-copilot-4.onrender.com

**GitHub Repository:** https://github.com/Devkhunger/seller-copilot

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS |
| Backend | Python, FastAPI |
| Data Processing | Pandas |
| Database | SQLite |
| Data Visualization | Recharts |
| AI Integration | Modular AI Service with Rule-Based Fallback |

## Core Features

### 1. CSV Upload & Data Processing
- Upload order datasets from Meesho, Flipkart, and Amazon.
- Automatically identify and clean inconsistent marketplace column names.
- Handle missing values and normalize order statuses.
- Prepare uploaded data for business analytics.

### 2. Business Intelligence Dashboard
- Total, delivered, cancelled and RTO orders.
- Revenue overview.
- Top-performing and underperforming SKUs.
- Advertisement-driven and organic orders.

### 3. SKU Performance Scoring
Evaluates individual products using order volume, delivery rate, RTO rate and cancellation rate.

- **Push:** Strong-performing products.
- **Watch:** Products requiring monitoring.
- **Pause:** Poor-performing products.

### 4. RTO Risk Shield
Identifies higher-RTO segments using:
- State-wise analysis.
- SKU-wise analysis.
- State and SKU combinations.
- Order-source-wise RTO patterns.

### 5. Promotion Recommender
Recommends products to promote, pause or improve and identifies safer state-product combinations.

### 6. AI Business Summary
Generates daily business summaries and actionable recommendations, with a rule-based fallback when an external LLM API is unavailable.

### 7. Listing Doctor
Generates:
- SEO-friendly product titles.
- Product descriptions.
- Selling-point bullets.
- Search keywords.
- Platform-specific listing content.

### 8. Inventory Management
Uses average daily order volume to estimate stock requirements and generate inventory alerts.

### 9. Daily Action Checklist
Stores business recommendations and daily tasks in SQLite and tracks completed actions.

### 10. Usage Tracking
Tracks uploads, dashboard views, completed actions, listing generation and inventory updates.

## SKU Scoring Methodology

```text
score = 50
      + delivered_rate * 30
      + normalized_order_volume * 20
      - rto_rate * 25
      - cancellation_rate * 15
```

All rates are decimal values between 0 and 1. The final score is clamped between 0 and 100.

| Score | Recommended Action |
|---|---|
| >= 75 | Push |
| >= 45 and < 75 | Watch |
| < 45 | Pause |

## RTO Risk Detection

A segment is classified as high-risk when:
- RTO rate >= 20%.
- Minimum 5 orders in the segment.

Analysis covers states, SKUs, state-SKU combinations and order sources.

## AI Service & Fallback Architecture

The AI functionality uses a modular service architecture.

- `backend/app/services/ai_service.py` handles business summary generation.
- `backend/app/services/listing_generator.py` handles listing generation.
- Checks for `OPENAI_API_KEY` or `LLM_API_KEY`.
- Uses rule-based generation when an API key is unavailable.

## Project Setup

### Backend

```bash
cd seller-copilot/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Backend: `http://localhost:8000`

### Frontend

```bash
cd seller-copilot/frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

## Configuration

Copy `.env.example` to `backend/.env` and `frontend/.env`. All variables are optional except `VITE_API_BASE` (frontend) in non-local deployments and `FRONTEND_ORIGINS` (backend) when the frontend is not on localhost.
Without `OPENAI_API_KEY` / `GEMINI_API_KEY` the app uses rule-based fallbacks.

## Running Tests

```bash
cd backend
pip install pytest httpx
python -m pytest -q tests
```

The same tests plus a frontend build run on every pull request (`.github/workflows/ci.yml`).

## Data & Security Notes

- The SQLite database (`*.db`) is created on first start and is git-ignored. Never commit it: it holds user accounts and order data.
- Load demo data by logging in and uploading `sample_data/sample_orders.csv`.
- Secrets go in `.env` files or the hosting dashboard, never in the repo.
- Deployment: see `DEPLOYMENT.md`. Release history: `docs/CHANGELOG.md`.

## Sample Dataset

```text
sample_data/sample_orders.csv
```

The frontend also exposes the sample at `/sample_data/sample_orders.csv`.

## Future Improvements

- Richer LLM-powered business recommendations.
- PostgreSQL for multi-seller production usage.
- Meesho, Flipkart and Amazon API integrations.
- WhatsApp-based daily business reports.
- Advanced ML-based RTO prediction.
- Demand forecasting and inventory optimization.

---

**AI Seller Copilot** transforms raw marketplace order data into practical business insights and actionable recommendations for small e-commerce sellers.
