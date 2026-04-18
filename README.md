# AI Seller Copilot for Small Ecommerce Sellers

AI Seller Copilot is a full-stack MVP that helps small ecommerce sellers upload Meesho, Flipkart, or Amazon order CSVs and answer:

**What should I do today to increase profitable orders and reduce losses?**

## Tech Stack

- Frontend: React + Vite + Tailwind CSS
- Backend: FastAPI
- Data processing: pandas
- Database: SQLite
- Charts: Recharts
- AI: modular `ai_service.py` with fallback rule-based summary and listing generation

## Features

- CSV upload and automatic cleaning for messy marketplace columns
- Dashboard summary with total, delivered, cancelled, RTO, revenue, top SKU, worst SKU, ad orders, and natural orders
- SKU score table with Push, Watch, and Pause actions
- RTO Risk Shield for states, SKUs, state + SKU combinations, and source-wise RTO
- Promotion recommender for SKUs to promote, pause, improve, and safe state/product combinations
- Daily AI business summary with rule-based fallback
- Listing Doctor for SEO title, description, bullets, keywords, and platform-specific text
- Daily action checklist stored in SQLite
- Inventory alerts using average daily orders
- Usage tracking for uploads, dashboard views, completed actions, listing generation, and stock updates

## Setup

### Backend

```bash
cd seller-copilot/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`.

### Frontend

```bash
cd seller-copilot/frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Sample CSV

Use:

```text
sample_data/sample_orders.csv
```

The frontend also exposes the same sample at `/sample_data/sample_orders.csv`.

## SKU Scoring Formula

For each SKU:

```text
score = 50
  + delivered_rate * 30
  + normalized_order_volume * 20
  - rto_rate * 25
  - cancellation_rate * 15
```

Rates are decimal values from `0` to `1`. `normalized_order_volume` is the SKU order volume divided by the highest SKU order volume in the uploaded file. The score is clamped between `0` and `100`.

Actions:

- `Push`: score >= 75
- `Watch`: score >= 45 and < 75
- `Pause`: score < 45

## RTO Risk Logic

High risk means:

- RTO rate >= 20%
- Minimum 5 orders in the segment

The app checks risk for states, SKUs, state + SKU combinations, and order sources.

## AI Fallback

`backend/app/services/ai_service.py` checks for `OPENAI_API_KEY` or `LLM_API_KEY`. If no key exists, the app uses rule-based summary generation so the MVP works locally without external services.

`backend/app/services/listing_generator.py` follows the same fallback pattern for the Listing Doctor.

## Future Improvements

- Real LLM integration for richer business recommendations
- PostgreSQL for multi-seller production usage
- Meesho, Flipkart, and Amazon platform API integrations
- WhatsApp daily report for sellers
- Advanced ML RTO prediction using customer location, price, SKU history, and source quality
update 26531
update 29480
update 24593
update 32514
update 27629
update 26431
update 1460
update 1561
update 21548
update 25955
update 9813
update 10076
update 13998
update 17488
update 23045
update 12565
update 13728
update 28740
update 19845
update 23544
update 8532
update 19404
update 19738
update 13896
update 27953
update 26456
update 25112
update 6863
update 5247
update 26646
update 19437
update 18990
update 9996
update 6333
update 30662
update 27614
