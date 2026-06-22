import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import ask, auth, dashboard, inventory, listing, ml, profit, upload, usage

load_dotenv()

app = FastAPI(title="AI Seller Copilot API")


def _frontend_origins() -> list[str]:
    raw = os.getenv("FRONTEND_ORIGINS", "")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if origins:
        return origins
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_frontend_origins(),
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(dashboard.router)
app.include_router(listing.router)
app.include_router(inventory.router)
app.include_router(usage.router)
app.include_router(ask.router)
app.include_router(ml.router)
app.include_router(profit.router)
